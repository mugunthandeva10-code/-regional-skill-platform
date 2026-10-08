# Regional Skill Intelligence Platform

A decision-support platform connecting regional employer demand with student action — **not** a job portal and **not** a chatbot.

## What it does

- Shows students what skills employers in their region actually need
- Compares those requirements against the student's current skills
- Identifies and prioritizes skill gaps with explainable reasoning
- Generates a personalized 6-week LEARN → BUILD → PROVE roadmap
- Lets students track progress and attach project proof (GitHub, demo links, screenshots)

## Architecture

```
Frontend (Next.js + React + TypeScript + Tailwind CSS + Recharts)
   |  REST
   v
Backend (Python + FastAPI + SQLAlchemy async + Pydantic)
   |--- Auth (JWT HS256, bcrypt)
   |--- Student profiles / skills / projects / resume parsing
   |--- Jobs, Skills, Regions, Roles, Sectors
   |--- Regional Demand Engine (data-driven, configurable formula)
   |--- Skill Gap Engine (Matched / Partial / Missing)
   |--- Priority Engine (transparent score + reason)
   |--- Roadmap Generator (templates + AI-personalized text)
   |--- AI Service Abstraction (swap provider without rewriting app code)
   |
   v
Database (PostgreSQL)
```

## Design

- Navy / dark blue + blue + orange accent + white cards
- Dashboard-oriented, student-friendly, responsive
- Mobile: vertical card layout

## Quick start (dev)

### Prerequisites

- Node.js 18+
- Python **3.11 or 3.12** (3.13/3.14 are not yet supported by SQLAlchemy 2.0)
- PostgreSQL

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set DATABASE_URL, SECRET_KEY, and any AI provider keys
uvicorn app.main:app --reload --port 8000
```

Backend runs at http://localhost:8000. API docs: http://localhost:8000/docs

> **No Postgres handy?** You can point the backend at a local SQLite file instead:
>
> ```bash
> DATABASE_URL="sqlite+aiosqlite:///./local.db" DEMO_AUTO_SEED=true \
>   .venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
> ```
>
> The app uses a portable `Uuid` column type, so the same models work on Postgres (production) and SQLite (quick local runs/tests). Install `aiosqlite` for this.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Frontend runs at http://localhost:3000.

### Docker (optional)

```bash
docker compose up -d
```

This starts PostgreSQL, the backend, and the frontend. Backend will auto-seed demo data on first start.

## Demo mode

The app ships with a complete labelled demo dataset (5 regions, 10 roles, 6 sectors, ~50 skills, ~30 demo jobs, pre-calculated demand) and a demo-student quick-entry path. Demo data is clearly marked "DEMO DATA" in the UI and in API responses. It must not be presented as live market data.

Demo student account (pre-seeded):

- Email: `student@demo.local`
- Password: `demo1234`
- Profile target: Backend Developer, Chennai

## API docs

Once the backend is running: http://localhost:8000/docs

## Key flows

1. Student registers (name, email, password, college, department, degree, graduation year, location, optional target role).
2. Student completes onboarding: preferred region, target role, target sector, summary.
3. Student adds skills manually OR uploads a resume PDF to extract skills.
4. Resume processing: extract text → extract skills → normalize → match against taxonomy → show to student → student confirms/edits. AI never silently adds skills.
5. Student dashboard shows: target role, region, readiness %, market demand skills, your skills, missing skills, top priority, roadmap progress, charts.
6. Demand page: filter by region / role / sector / time window. Shows demand %, job count, confidence, evidence, and scoring formula.
7. Skill gap page: Matched / Partial / Missing, sorted by priority, with detail panel and "why this matters" reasoning.
8. Roadmap page: 6-week timeline with LEARN / BUILD / PROVE status per stage, project link, mark complete.
9. Projects page: create/edit projects, attach GitHub, demo link, screenshot.
10. Admin dashboard: total students, jobs, skills, regions, roles, sectors, top demanded skills, most selected roles, average gaps, data quality.
11. Admin jobs / skills / data pages: CRUD and CSV import.

## Technology stack

- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts, Lucide icons, Axios
- Backend: FastAPI, SQLAlchemy (async), Pydantic, Pydantic Settings, python-jose, passlib/bcrypt, PyPDF2
- Database: PostgreSQL
- AI: provider abstraction layer; OpenAI/LiteLLM optional; rule-based + templates as always-available fallback

## Database schema (core tables)

- users
- student_profiles
- regions, roles, sectors
- skills, skill_aliases
- student_skills
- resumes
- projects
- job_postings, job_skills
- skill_evidence
- skill_gaps
- roadmaps, roadmap_items

Key indexes: jobs by region/role/sector/city/date, job_skills by job/skill, student_skills by user/skill, skill_evidence by region+role+skill.

## API design

Auth: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `PUT /auth/me`

Student: `GET/PUT /students/profile`, `POST /students/resume`, `GET/PUT /students/skills`, `DELETE /students/skills/{skill_id}`, `GET /students/options`, `POST/GET/PUT /students/projects`

Projects (top-level alias): `GET /projects`, `POST /projects`, `PUT /projects/{id}`

Jobs: `GET /jobs`, `GET /jobs/{id}`, `POST /jobs`, `PUT /jobs/{id}`, `DELETE /jobs/{id}`, `POST /admin/import-jobs`, `POST /admin/seed-demo`

Demand: `GET /demand`, `GET /demand/{region_id}/{role_id}`

Gaps: `GET /skill-gap`, `POST /skill-gap/analyze`

Roadmap: `GET /roadmap`, `POST /roadmap/generate`, `PUT /roadmap/items/{id}`, `GET /roadmap/{skill_name}/project-recommendation`

Skills taxonomy: `GET/POST/PUT/DELETE /skills`, `GET /skills/{id}/aliases`, `GET/POST/PUT /regions`, `GET/POST/PUT /roles`, `GET/POST/PUT /sectors`

Admin: `GET /admin/statistics`, `GET /admin/data-quality`

## AI architecture

The AI layer is a separate module with a provider abstraction:

- `extract_skills(text)` — resume skill extraction (optional; rule-based always available)
- `normalize_skill(name)` — rule-based canonicalization (deterministic, auditable)
- `explain_recommendation(skill, demand, gap, reason)` — generates "why this skill" text
- `generate_roadmap_text(...)` — personalization of roadmap notes
- `generate_project_recommendation(skill, context)` — project ideas

Provider selection is via `settings.llm_provider`. If unset or unreachable, the system uses the demo/rule-based service and never invents job statistics.

Regional demand is **always** computed from structured data, never from the LLM.

## AI prompt safety / reliability

AI responses:

- Use only supplied evidence
- Never invent job statistics
- Clearly distinguish demo data
- Mention low confidence when data is insufficient
- Avoid claiming guaranteed employment or definite job outcomes

If evidence is insufficient: "No reliable regional evidence is available for this recommendation."

## Fallback logic

- Resume AI extraction fails → allow manual skill entry
- Regional data unavailable → use broader region data with a confidence indicator
- AI roadmap generation fails → use predefined roadmap templates
- Database empty → load demo dataset

## Security

- Password hashing with bcrypt via passlib
- JWT authentication with configurable expiration
- Role-based access: student vs admin
- Input validation on all endpoints
- File upload validation: PDF only, size limit
- Environment variables for secrets; no API keys in frontend
- CORS configured for dev (restrict in production)

## Responsive design

Works on desktop, laptop, tablet, and mobile. Mobile dashboard uses vertical card layout.

## Required pages

- / — Landing page
- /login — Login
- /register — Registration
- /onboarding — Student setup
- /dashboard — Student dashboard
- /profile — Student profile
- /skills — Student skills (add / edit levels / import from resume)
- /demand — Regional demand
- /gap — Skill gap
- /roadmap — Personal roadmap
- /projects — Projects/proof
- /admin — Admin dashboard
- /admin/jobs — Job management
- /admin/skills — Skill management
- /admin/data — Data management

## Data quality

Shows: jobs analyzed, jobs with skill extraction, unique skills, last refresh, % with extracted skills, confidence level, demo data flag, and a note about limitations. Limitations are never hidden.

## Privacy

Minimizes personal data. Resumes are stored per-user and not exposed publicly. Student data is not exposed to other students. Aggregated/anonymized information is used for regional demand.

## Error handling

Handles: invalid login, missing profile, resume extraction failure, unsupported PDF, no job data, no regional data, low-confidence data, AI API failure, database failure. If AI fails, the application still shows rule-based / template-based recommendations.

## MVP limitation

The MVP proves: Student Profile → Regional Demand → Skill Gap → Explainable Priority → Personalized Roadmap → Project Proof. It uses a limited set of regions, roles, and skills, and is architected so more can be added later. It does not attempt to model the entire employment ecosystem.

## Final success criteria

A judge can:

1. Register as a student
2. Select Chennai
3. Select Backend Developer
4. Enter/upload skills
5. See regional job demand
6. See their skill gaps
7. Understand WHY a skill is recommended
8. See a priority ranking
9. Receive a 6-week roadmap
10. Build/attach project proof
11. Track roadmap progress

The complete demo takes under 5 minutes.

## Tests

Run with:

```bash
cd backend
.venv/Scripts/python.exe -m pytest tests -q
```

The tests are **self-contained**: they create a temporary SQLite database and seed the demo dataset, so no running PostgreSQL is required. 74 tests currently pass.

They cover:

- Authentication (register, login, duplicate, invalid login, me, admin-only access)
- Skill normalization (aliases, canonical forms)
- Resume extraction (rule-based candidates, confidence, common skills)
- Demand formula (weights, scores, confidence flags)
- Demand integration (percentages are relative to **total** relevant jobs)
- Gap severity + priority scoring + explanations
- Roadmap templates and project recommendations
- `PUT /auth/me` personal-info updates
- API endpoint smoke tests

## Deployment

- Use a real PostgreSQL instance
- Set a strong `SECRET_KEY`
- Restrict CORS origins
- Run Alembic migrations instead of `metadata.create_all` in production
- Use a managed or self-hosted LLM provider if desired; the app works without one
- Restrict upload directory and validate file types

## Limitations

- Demo data is curated, not live market data
- Resume parsing is rule-based by default; AI extraction is optional
- Regional demand depends on the quality/quantity of job postings in the dataset
- Small-city data may be low confidence and falls back to broader regions

## Future improvements

- Add more regions, roles, sectors, institutions
- Real-time or scheduled job data ingestion from approved sources
- Improved resume parsing with OCR and layout-aware extraction
- Student portfolio showcase
- Employer/emprove side (future)
- Skill dependency graph
- Recommendation explainability with source citations
- Analytics for colleges/regions
