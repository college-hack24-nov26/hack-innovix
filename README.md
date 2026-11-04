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
| Patient| patient@medikiosk.com     | Patient123!  |
| Doctor | dr.sharma@medikiosk.com   | Clinic@2026  |
| Triage | triage@medikiosk.com      | Triage123!   |
| Admin  | admin@medikiosk.com       | Admin123!    |

New patients can also use **Register**. Consent is required before the interview.

### Doctor login and registration

- Doctors sign in at `/doctor/login` (linked from the home page and the top bar). Patient accounts are turned away there.
- New doctors register at `/doctor/register` (open sign-up, no invite code).
- In the doctor portal, **Patients** lists each patient's login email, account status and last login (searchable by email), and the patient's **Overview** tab shows registration date, last login and login count. Passwords are never shown.
- **Excel copy of users:** every doctor/patient registration (and the seed script) rebuilds `instance/exports/medikiosk_users.xlsx` from the database, with a *Doctors* and a *Patients* sheet. Doctors can also download it from **Patients → Download Excel**. No passwords or hashes are written. Close the file in Excel before registering new users, or the update is skipped (the app logs it and carries on).

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
