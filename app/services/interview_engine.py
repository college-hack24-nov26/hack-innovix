"""Adaptive clinical interviewer: next question depends on prior answers."""

from __future__ import annotations

import json
import re

from sqlalchemy.orm.attributes import flag_modified

INTERVIEW_SYSTEM = (
    "You are an expert hospital case-taking interviewer. You collect history only. "
    "You never diagnose, never prescribe, never invent facts. "
    "Ask one question at a time. Tailor it to this patient's problem and previous answers. "
    "Do not use the same generic script for every patient. "
    "If the complaint is fever, do not ask pain-radiation questions. "
    "If the complaint is chest pain, focus on cardiac/respiratory history. "
    "Return ONLY compact JSON with keys: done (boolean), key, section, prompt, options (array of short strings). "
    "When HPI is sufficient, ask past medical history, then medicines, then allergies, then set done true. "
    "Maximum 12 questions including those already asked."
)

MAX_QUESTIONS = 12

CHIEF = {
    "key": "chief_complaint",
    "section": "Chief Complaint",
    "prompt": "What is the main problem that brought you in today?",
    "type": "chips",
    "options": [
        "Chest Pain",
        "Fever",
        "Cough",
        "Breathing Difficulty",
        "Headache",
        "Abdominal Pain",
        "Weakness",
        "Other",
    ],
}

PATHWAYS: dict[str, list[dict]] = {
    "chest_pain": [
        {
            "key": "onset",
            "section": "History of Present Illness",
            "prompt": "When did the chest pain start?",
            "type": "chips",
            "options": ["Minutes ago", "A few hours ago", "Today", "A few days ago", "Longer than a week"],
        },
        {
            "key": "location",
            "section": "History of Present Illness",
            "prompt": "Where do you feel the chest pain?",
            "type": "chips",
            "options": ["Centre of the chest", "Left side", "Right side", "Spreads across the chest", "Not sure"],
        },
        {
            "key": "character",
            "section": "History of Present Illness",
            "prompt": "What does the chest pain feel like?",
            "type": "chips",
            "options": ["Pressure or heaviness", "Sharp", "Burning", "Tightness", "Tearing"],
        },
        {
            "key": "severity",
            "section": "History of Present Illness",
            "prompt": "How severe is the chest pain from 1 (mild) to 10 (worst)?",
            "type": "chips",
            "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        },
        {
            "key": "radiation",
            "section": "History of Present Illness",
            "prompt": "Does the chest pain spread to the arm, neck, jaw, or back?",
            "type": "chips",
            "options": ["Left arm", "Jaw or neck", "Back", "Does not spread"],
        },
        {
            "key": "associated",
            "section": "History of Present Illness",
            "prompt": "With the chest pain, have you also had any of these?",
            "type": "chips",
            "options": ["Sweating", "Nausea or vomiting", "Shortness of breath", "Dizziness", "None of these"],
        },
        {
            "key": "aggravating",
            "section": "History of Present Illness",
            "prompt": "What makes the chest pain worse?",
            "type": "chips",
            "options": ["Walking or effort", "Breathing in", "Lying down", "After food", "Nothing in particular"],
        },
    ],
    "fever": [
        {
            "key": "onset",
            "section": "History of Present Illness",
            "prompt": "When did the fever start?",
            "type": "chips",
            "options": ["Today", "Yesterday", "2–3 days ago", "About a week", "Longer"],
        },
        {
            "key": "fever_pattern",
            "section": "History of Present Illness",
            "prompt": "How is the fever behaving?",
            "type": "chips",
            "options": ["Continuous", "Comes and goes", "Only at night", "With chills", "Not sure"],
        },
        {
            "key": "severity",
            "section": "History of Present Illness",
            "prompt": "If it was measured, about how high was the temperature?",
            "type": "chips",
            "options": ["Not measured", "Mild", "High", "Very high", "With shivering"],
        },
        {
            "key": "associated",
            "section": "History of Present Illness",
            "prompt": "Along with fever, what else is present?",
            "type": "chips",
            "options": ["Cough", "Sore throat", "Headache", "Burning urine", "Rash", "Loose stools", "None of these"],
        },
        {
            "key": "relieving",
            "section": "History of Present Illness",
            "prompt": "Does anything bring the fever down?",
            "type": "chips",
            "options": ["Paracetamol / fever medicine", "Sponge bath", "Nothing helps", "Not tried"],
        },
    ],
    "cough": [
        {
            "key": "onset",
            "section": "History of Present Illness",
            "prompt": "How long have you had this cough?",
            "type": "chips",
            "options": ["A few days", "About a week", "2–3 weeks", "More than a month"],
        },
        {
            "key": "character",
            "section": "History of Present Illness",
            "prompt": "What is the cough like?",
            "type": "chips",
            "options": ["Dry", "With phlegm", "With blood", "Worse at night", "With wheeze"],
        },
        {
            "key": "associated",
            "section": "History of Present Illness",
            "prompt": "With the cough, do you also have fever, chest pain, or breathlessness?",
            "type": "chips",
            "options": ["Fever", "Chest pain", "Breathlessness", "Weight loss", "None of these"],
        },
        {
            "key": "aggravating",
            "section": "History of Present Illness",
            "prompt": "What makes the cough worse?",
            "type": "chips",
            "options": ["Dust or smoke", "Lying down", "Exercise", "Cold air", "Not sure"],
        },
        {
            "key": "substance",
            "section": "Personal History",
            "prompt": "Do you smoke or have you smoked in the past?",
            "type": "chips",
            "options": ["Currently smoke", "Used to smoke", "Never smoked", "Prefer not to say"],
        },
    ],
    "breathing": [
        {
            "key": "onset",
            "section": "History of Present Illness",
            "prompt": "When did the breathing difficulty start?",
            "type": "chips",
            "options": ["Suddenly today", "Over a few days", "For weeks", "For months"],
        },
        {
            "key": "character",
            "section": "History of Present Illness",
            "prompt": "When is the breathing most difficult?",
            "type": "chips",
            "options": ["At rest", "While walking", "At night", "When lying flat", "During cough"],
        },
        {
            "key": "associated",
            "section": "History of Present Illness",
            "prompt": "With the breathing difficulty, is there chest pain, wheeze, or swelling of the legs?",
            "type": "chips",
            "options": ["Chest pain", "Wheeze", "Leg swelling", "Fever", "None of these"],
        },
        {
            "key": "severity",
            "section": "History of Present Illness",
            "prompt": "Can you speak a full sentence without stopping for breath?",
            "type": "chips",
            "options": ["Yes", "Only a few words", "Cannot speak comfortably", "Not sure"],
        },
    ],
    "headache": [
        {
            "key": "onset",
            "section": "History of Present Illness",
            "prompt": "How did the headache begin?",
            "type": "chips",
            "options": ["Suddenly (seconds to minutes)", "Over hours", "Over days", "Recurring for weeks"],
        },
        {
            "key": "location",
            "section": "History of Present Illness",
            "prompt": "Where is the headache?",
            "type": "chips",
            "options": ["Whole head", "One side", "Forehead or eyes", "Back of the head", "Neck"],
        },
        {
            "key": "severity",
            "section": "History of Present Illness",
            "prompt": "Is this the worst headache you have ever had?",
            "type": "chips",
            "options": ["Yes", "Severe but not the worst", "Moderate", "Mild"],
        },
        {
            "key": "associated",
            "section": "History of Present Illness",
            "prompt": "With the headache, is there fever, neck stiffness, vomiting, or vision change?",
            "type": "chips",
            "options": ["Fever", "Neck stiffness", "Vomiting", "Vision change", "None of these"],
        },
        {
            "key": "aggravating",
            "section": "History of Present Illness",
            "prompt": "What makes the headache worse?",
            "type": "chips",
            "options": ["Light or sound", "Coughing", "Stress", "Lack of sleep", "Not sure"],
        },
    ],
    "abdominal": [
        {
            "key": "onset",
            "section": "History of Present Illness",
            "prompt": "When did the abdominal pain start?",
            "type": "chips",
            "options": ["Last few hours", "Today", "A few days", "Off and on for weeks"],
        },
        {
            "key": "location",
            "section": "History of Present Illness",
            "prompt": "Where in the abdomen is the pain?",
            "type": "chips",
            "options": ["Upper", "Around the navel", "Lower right", "Lower left", "All over"],
        },
        {
            "key": "character",
            "section": "History of Present Illness",
            "prompt": "What is the pain like?",
            "type": "chips",
            "options": ["Cramping", "Constant", "Burning", "Sharp", "Comes in waves"],
        },
        {
            "key": "associated",
            "section": "History of Present Illness",
            "prompt": "With the abdominal pain, is there vomiting, fever, or a change in stools?",
            "type": "chips",
            "options": ["Vomiting", "Fever", "Loose stools", "Constipation", "Blood in stool", "None of these"],
        },
        {
            "key": "aggravating",
            "section": "History of Present Illness",
            "prompt": "Does food, movement, or passing stool change the pain?",
            "type": "chips",
            "options": ["Worse after food", "Better after food", "Worse with movement", "No change"],
        },
    ],
    "weakness": [
        {
            "key": "onset",
            "section": "History of Present Illness",
            "prompt": "When did the weakness start?",
            "type": "chips",
            "options": ["Suddenly", "Over hours", "Over days", "Gradually over weeks"],
        },
        {
            "key": "location",
            "section": "History of Present Illness",
            "prompt": "Which part of the body feels weak?",
            "type": "chips",
            "options": ["One arm or leg", "One side of the body", "Face", "Whole body", "Not sure"],
        },
        {
            "key": "associated",
            "section": "History of Present Illness",
            "prompt": "Is there facial droop, speech difficulty, or loss of consciousness?",
            "type": "chips",
            "options": ["Face droop", "Speech difficulty", "Loss of consciousness", "Numbness", "None of these"],
        },
        {
            "key": "severity",
            "section": "History of Present Illness",
            "prompt": "Can you walk and use your arms as usual?",
            "type": "chips",
            "options": ["Yes", "Walking is difficult", "Cannot use a limb", "Need help for everything"],
        },
    ],
    "general": [
        {
            "key": "onset",
            "section": "History of Present Illness",
            "prompt": "When did this problem start?",
            "type": "chips",
            "options": ["Today", "A few days", "About a week", "Longer than a month"],
        },
        {
            "key": "location",
            "section": "History of Present Illness",
            "prompt": "Where in the body is the problem most noticeable?",
            "type": "text",
            "options": [],
        },
        {
            "key": "character",
            "section": "History of Present Illness",
            "prompt": "How would you describe what you feel?",
            "type": "text",
            "options": [],
        },
        {
            "key": "severity",
            "section": "History of Present Illness",
            "prompt": "How much is this affecting you from 1 to 10?",
            "type": "chips",
            "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        },
        {
            "key": "associated",
            "section": "History of Present Illness",
            "prompt": "Any other symptoms along with this problem?",
            "type": "text",
            "options": [],
        },
    ],
}

SHARED = [
    {
        "key": "past_medical",
        "section": "Past Medical History",
        "prompt": "Do you have any long-term conditions such as diabetes, blood pressure, heart disease, or asthma?",
        "type": "chips",
        "options": ["Diabetes", "Blood pressure", "Heart disease", "Asthma", "None", "Other"],
    },
    {
        "key": "medications",
        "section": "Medication History",
        "prompt": "What medicines are you taking now, if any?",
        "type": "text",
        "options": [],
    },
    {
        "key": "allergies",
        "section": "Allergy History",
        "prompt": "Do you have any medicine or food allergies?",
        "type": "chips",
        "options": ["No known allergies", "Medicine allergy", "Food allergy", "Not sure"],
    },
]

CONDITIONAL = [
    {
        "key": "diabetes_followup",
        "section": "Past Medical History",
        "prompt": "For diabetes, do you know a recent blood sugar or HbA1c value?",
        "type": "text",
        "options": [],
        "if_any": ["diabetes", "sugar"],
        "after": "past_medical",
    },
    {
        "key": "investigations",
        "section": "Previous Investigations",
        "prompt": "Have you had any recent ECG, blood tests, X-ray, or scans for this problem?",
        "type": "chips",
        "options": ["Yes", "No", "Not sure"],
        "pathways": ["chest_pain", "breathing", "cough"],
        "after": "allergies",
    },
    {
        "key": "past_surgical",
        "section": "Past Surgical History",
        "prompt": "Have you had any operations in the past?",
        "type": "chips",
        "options": ["No", "Yes"],
        "after": "past_medical",
        "skip_if_none": "past_medical",
    },
]

AYUSH_FLOW = [
    {"key": k, "section": "AYUSH Assessment", "prompt": prompt, "type": "text", "options": []}
    for k, prompt in (
        ("prakriti", "Prakriti (constitution), if known"),
        ("vikriti", "Vikriti (current imbalance), if known"),
        ("ahara", "Usual diet (Ahara)"),
        ("vihara", "Daily routine and activity (Vihara)"),
        ("nidana", "What do you feel led to this problem (Nidana)?"),
    )
]


def classify_complaint(text: str) -> str:
    t = (text or "").lower()
    if any(w in t for w in ("chest pain", "chest discomfort", "angina", "pressure in chest")):
        return "chest_pain"
    if any(w in t for w in ("breath", "dyspnea", "shortness of breath", "breathing")):
        return "breathing"
    if "fever" in t or "temperature" in t:
        return "fever"
    if "cough" in t:
        return "cough"
    if any(w in t for w in ("headache", "migraine")):
        return "headache"
    if any(w in t for w in ("abdomen", "stomach", "belly", "abdominal")):
        return "abdominal"
    if any(w in t for w in ("weakness", "stroke", "paralysis", "face droop", "speech")):
        return "weakness"
    if "pain" in t:
        return "abdominal" if any(w in t for w in ("stomach", "tummy", "urine")) else "general"
    return "general"


def answers_map(session) -> dict[str, str]:
    return {a.question_key: (a.value or "") for a in session.answers}


def _meta(session) -> dict:
    raw = session.missing_fields
    return raw if isinstance(raw, dict) else {}


def _save_meta(session, meta: dict) -> None:
    session.missing_fields = dict(meta)
    flag_modified(session, "missing_fields")


def _none_like(value: str) -> bool:
    t = (value or "").strip().lower()
    return t in {"", "none", "no", "nil", "n/a", "na", "none of these", "no known allergies"}


def _blob(answers: dict[str, str]) -> str:
    return " ".join(answers.values()).lower()


def _should_skip(question: dict, answers: dict[str, str], pathway: str) -> bool:
    key = question["key"]
    if key in answers:
        return True
    allowed = question.get("pathways")
    if allowed and pathway not in allowed:
        return True
    after = question.get("after")
    if after and after not in answers:
        return True
    if question.get("skip_if_none") and _none_like(answers.get(question["skip_if_none"], "")):
        return True
    needles = question.get("if_any")
    if needles and not any(n in _blob(answers) for n in needles):
        return True
    return False


def _pathway_questions(pathway: str) -> list[dict]:
    return list(PATHWAYS.get(pathway) or PATHWAYS["general"])


def expert_next_question(session, answers: dict[str, str]) -> dict | None:
    if "chief_complaint" not in answers:
        return dict(CHIEF)

    pathway = classify_complaint(answers.get("chief_complaint") or "")
    meta = _meta(session)
    meta["pathway"] = pathway

    asked_n = len([k for k in answers if answers.get(k)])
    if asked_n >= MAX_QUESTIONS and not session.ayush_enabled:
        _save_meta(session, meta)
        return None

    sequence: list[dict] = _pathway_questions(pathway) + list(SHARED) + list(CONDITIONAL)
    if session.ayush_enabled:
        sequence += AYUSH_FLOW

    for question in sequence:
        if _should_skip(question, answers, pathway):
            continue
        if asked_n >= MAX_QUESTIONS and question.get("key") in {q["key"] for q in AYUSH_FLOW}:
            continue
        _save_meta(session, meta)
        return {
            "key": question["key"],
            "section": question["section"],
            "prompt": question["prompt"],
            "type": question.get("type") or ("chips" if question.get("options") else "text"),
            "options": question.get("options") or [],
        }

    _save_meta(session, meta)
    return None


def _parse_ai_question(raw: str) -> dict | None:
    if not raw:
        return None
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if data.get("done"):
        return {"done": True}
    prompt = (data.get("prompt") or "").strip()
    key = re.sub(r"[^a-z0-9_]+", "_", (data.get("key") or "follow_up").lower()).strip("_")[:80]
    if not prompt or not key:
        return None
    options = data.get("options") or []
    if not isinstance(options, list):
        options = []
    options = [str(o)[:80] for o in options][:8]
    return {
        "key": key,
        "section": data.get("section") or "History of Present Illness",
        "prompt": prompt[:400],
        "type": "chips" if options else "text",
        "options": options,
        "done": False,
    }


def _ai_next_question(session, answers: dict[str, str]) -> dict | None:
    from flask import current_app, has_app_context

    from app.ai import get_ai_provider
    from app.ai.mock_provider import MockAIProvider

    if not has_app_context():
        return None
    if current_app.config.get("AI_PROVIDER", "mock").lower() != "openai":
        return None
    if not current_app.config.get("OPENAI_API_KEY"):
        return None
    provider = get_ai_provider()
    if isinstance(provider, MockAIProvider):
        return None

    asked = [{"key": k, "answer": v} for k, v in answers.items()]
    user = (
        f"Language: {(session.patient.language if session.patient else 'en')}\n"
        f"Chief complaint: {answers.get('chief_complaint')}\n"
        f"Pathway hint: {classify_complaint(answers.get('chief_complaint') or '')}\n"
        f"Answers so far ({len(asked)}): {json.dumps(asked, ensure_ascii=False)}\n"
        "Propose the single next history question. Do not repeat a key already answered."
    )
    try:
        raw = provider.complete(INTERVIEW_SYSTEM, user, temperature=0.35)
    except Exception:
        return None
    parsed = _parse_ai_question(raw)
    if not parsed or parsed.get("done"):
        return None if not parsed else parsed
    if parsed["key"] in answers:
        return None
    return parsed


def next_question(session, answers: dict[str, str] | None = None) -> dict | None:
    answers = answers if answers is not None else answers_map(session)
    pending = _meta(session).get("pending")
    if isinstance(pending, dict) and pending.get("key") and pending["key"] not in answers:
        return pending

    ai_q = _ai_next_question(session, answers)
    if ai_q and ai_q.get("done"):
        return None
    if ai_q:
        meta = _meta(session)
        meta["pending"] = ai_q
        _save_meta(session, meta)
        return ai_q

    expert = expert_next_question(session, answers)
    meta = _meta(session)
    meta["pending"] = expert
    _save_meta(session, meta)
    return expert


def progress_for(session, answers: dict[str, str]) -> tuple[int, int, int]:
    pathway = classify_complaint(answers.get("chief_complaint") or "")
    planned = 1 + len(_pathway_questions(pathway)) + len(SHARED)
    if session.ayush_enabled:
        planned += len(AYUSH_FLOW)
    planned = min(planned, MAX_QUESTIONS + (len(AYUSH_FLOW) if session.ayush_enabled else 0))
    answered = len(answers)
    index = min(answered + 1, planned)
    percent = int(100 * answered / max(planned, 1))
    return index, planned, min(percent, 99 if answered < planned else 100)
