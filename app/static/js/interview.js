import { api, toast } from "./main.js";
import { createRecognizer, speak } from "./voice.js";

const root = document.getElementById("interview-root");
if (root) {
  const sessionId = Number(root.dataset.sessionId);
  const lang = root.dataset.lang || "en";
  const promptEl = document.getElementById("q-prompt");
  const sectionEl = document.getElementById("q-section");
  const progressEl = document.getElementById("q-progress");
  const counterEl = document.getElementById("q-counter");
  const input = document.getElementById("q-input");
  const chips = document.getElementById("q-chips");
  const emergency = document.getElementById("emergency-banner");
  const micBtn = document.getElementById("mic-btn");
  const speakBtn = document.getElementById("speak-btn");
  const nextBtn = document.getElementById("next-btn");
  const voiceHint = document.getElementById("voice-hint");

  let currentKey = null;
  let rec = createRecognizer({
    lang,
    onResult: (t) => { input.value = t; input.focus(); },
    onStart: () => micBtn.classList.add("listening"),
    onEnd: () => micBtn.classList.remove("listening"),
    onUnavailable: () => { voiceHint.hidden = false; micBtn.disabled = true; },
  });

  async function renderFrom(payload) {
    if (payload.emergency) {
      emergency.hidden = false;
      emergency.textContent = payload.patient_message || emergency.dataset.default;
    }
    if (payload.done) {
      promptEl.textContent = "Intake complete. You can review and submit.";
      chips.innerHTML = "";
      nextBtn.textContent = "Review";
      nextBtn.onclick = () => { window.location.href = "/patient/review"; };
      progressEl.style.width = "100%";
      return;
    }
    const q = payload.question;
    currentKey = q.key;
    promptEl.textContent = q.prompt;
    sectionEl.textContent = q.section;
    input.value = "";
    progressEl.style.width = `${payload.progress}%`;
    counterEl.textContent = `${payload.index} / ${payload.total}`;
    chips.innerHTML = "";
    (q.options || []).forEach((opt) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.textContent = opt;
      b.addEventListener("click", () => { input.value = opt; });
      chips.appendChild(b);
    });
  }

  async function load() {
    const payload = await api(`/api/interview/${sessionId}/next-question`);
    renderFrom(payload);
  }

  nextBtn.addEventListener("click", async () => {
    if (!currentKey) return;
    const payload = await api(`/api/interview/${sessionId}/answer`, {
      method: "POST",
      body: JSON.stringify({ question_key: currentKey, value: input.value, source: "text" }),
    });
    renderFrom(payload);
  });

  micBtn.addEventListener("click", () => {
    if (!rec) return;
    try { rec.start(); } catch (e) { toast("Microphone busy"); }
  });
  speakBtn.addEventListener("click", () => speak(promptEl.textContent, lang));

  load().catch(() => toast("Could not load interview"));
}
