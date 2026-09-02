<<<<<<< HEAD
# TEMPLATE
=======
# MediKiosk

AI-powered multilingual patient case-taking and medical document intelligence for hospitals. It collects structured history before a consultation, extracts text from uploaded reports, flags urgent symptom patterns for triage, and produces a physician-reviewed draft summary.

This software is a clinical documentation aid. It does not diagnose, prescribe, or replace a licensed clinician.

## Stack

- Python 3.11, Flask, Jinja2, SQLAlchemy, Flask-Login
- SQLite for local demo; PostgreSQL in Docker
- Mock AI and Mock OCR by default (no API key required)
- Optional OpenAI and Tesseract via environment variables

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python seed/seed_data.py
python run.py
```

Open http://127.0.0.1:5000

### Demo accounts

| Role   | Email                     | Password     |
|--------|---------------------------|--------------|
| Patient| patient@medikiosk.local   | Patient123!  |
| Doctor | doctor@medikiosk.local    | Doctor123!   |
| Triage | triage@medikiosk.local    | Triage123!   |
| Admin  | admin@medikiosk.local     | Admin123!    |

New patients can also use **Register**. Consent is required before the interview.

## Configuration

See `.env.example`.

- `AI_PROVIDER=mock|openai|local`
- `OCR_PROVIDER=mock|tesseract`
- `DATABASE_URL=sqlite:///medikiosk.db` or PostgreSQL URL

## Tests

```bash
pytest
```

## Docker

```bash
docker compose up --build
```

Gunicorn serves the app on port 8000.

## Architecture

Browser → Jinja templates + vanilla JS → Flask routes/API → services → AI/OCR/speech → SQLAlchemy → SQLite/PostgreSQL.

FHIR export and ABDM sync are demo integrations (local bundle / simulated sync). Identification options include hospital ID, ABHA ID, and a clearly labelled simulated ID. There is no Aadhaar authentication.

## Languages

English, Hindi, and Marathi dictionaries live in `translations/`. Templates use `{{ _('key') }}`.
>>>>>>> d58c00e (initial commit)
