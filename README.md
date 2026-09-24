# Smart Attendance Management System

A full-stack attendance management system for a college (~5,000 students,
~200 faculty), built using **Spec-Driven Development** — see
[`docs/sdd/`](docs/sdd/) for the specification-by-specification history and
[`docs/traceability-matrix.md`](docs/traceability-matrix.md) for requirement
→ test mapping.

**Status**: under active development. All backend specifications (SPEC
00–16) are complete — 166/166 backend tests passing. Frontend UI is in
progress; see the traceability matrix for current progress across all 18
specifications.

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full picture.
Summary: React (TypeScript) frontend talks to a layered FastAPI backend
(Router → Service → Repository → SQLAlchemy) over a JSON REST API; Google
Gemini is called server-side only for advisory AI insights.

## Technology Stack

**Backend**: Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2,
PyJWT, bcrypt, pytest.

**Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, React Router,
TanStack Query, Vitest + React Testing Library.

**Database**: SQLite for dev/test, PostgreSQL-compatible for production
(see Assumption A-1 in [`docs/sdd/00-product-spec.md`](docs/sdd/00-product-spec.md)).

**AI**: Google Gemini, backend-only integration (SPEC 15).

## Prerequisites

- Python 3.12+
- Node.js 20+ and npm
- (Production only) a PostgreSQL server — not required for local dev/test.

## Backend setup

```bash
cd backend
python -m venv venv
./venv/Scripts/activate        # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements-dev.txt
cp .env.example .env           # then fill in JWT_SECRET at minimum
```

### Environment variables (`backend/.env`)

| Variable | Purpose | Dev default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./dev.db` |
| `JWT_SECRET` | JWT signing secret — set a real random value | _(none — must be set)_ |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Access token lifetime | `60` |
| `GEMINI_API_KEY` | Google Gemini key (never committed) | _(empty — AI insights degrade gracefully)_ |
| `GEMINI_MODEL` | Gemini model name | `gemini-1.5-flash` |
| `GEMINI_TIMEOUT_SECONDS` | Timeout for Gemini calls | `10` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173` |
| `LOW_ATTENDANCE_DEFAULT_THRESHOLD` | Default low-attendance % threshold | `75.0` |
| `LOG_LEVEL` | Logging level | `INFO` |

Generate a real `JWT_SECRET`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Running the backend

```bash
cd backend
./venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

- Health check: `GET http://localhost:8000/health`
- Interactive API docs: `http://localhost:8000/docs`

### Database migrations

Introduced starting SPEC 04 once domain models exist:

```bash
cd backend
./venv/Scripts/alembic.exe upgrade head
```

### Seed data

Populates 3 departments, 24 faculty, 120 students across 6 sections, and
~3 weeks of realistic attendance history (`backend/scripts/seed.py`):

```bash
cd backend
./venv/Scripts/alembic.exe upgrade head   # tables must exist first
./venv/Scripts/python.exe scripts/seed.py
```

Every seeded account (admin, faculty, and student) uses the password
`Password123!` — see [Demo Credentials](#demo-credentials) below. Intended
for a fresh database; re-running against already-seeded data will fail on
duplicate emails/codes.

### Running backend tests

```bash
cd backend
./venv/Scripts/python.exe -m pytest -v
```

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL defaults to http://localhost:8000
npm run dev
```

Frontend dev server: `http://localhost:5173`

### Running frontend tests

```bash
cd frontend
npm test
```

### Build

```bash
cd frontend
npm run build
```

## Running E2E tests

Introduced starting SPEC 18 (Playwright), once the required workflows exist
end-to-end.

## User Roles

- **Admin** — full academic-structure management, user/role management,
  attendance review/correction approval, reports, threshold configuration.
- **Faculty** — record/submit attendance for assigned classes, request
  corrections, view their students' history and low-attendance lists.
- **Student** — view own attendance/history, submit correction requests.

See [`docs/sdd/00-product-spec.md`](docs/sdd/00-product-spec.md) §2–§4 for
full detail.

## Main Workflows

See [`docs/sdd/00-product-spec.md`](docs/sdd/00-product-spec.md) §3 and the
six required E2E workflows tracked in `docs/testing-strategy.md`.

## Demo Credentials

After running `scripts/seed.py`, every account uses the password
`Password123!`.

| Role | Email |
|---|---|
| Admin | `admin@college.edu` |
| Faculty | `faculty.cse1@college.edu` (or `faculty.ece1@`, `faculty.mech1@`, ... up to 8 per department) |
| Student | `student.csea001@college.edu` (roll number pattern `{DEPT}{SECTION}{NNN}`, e.g. `CSEA001`–`CSEA020`, `CSEB001`–`CSEB020`, similarly for ECE/MECH) |

## Known Limitations

Tracked and updated per spec; see each `docs/sdd/NN-*.md` file's own
"Defects Found" / acceptance sections, and the assumptions in
`docs/sdd/00-product-spec.md` §6 (e.g., SQLite for dev/test, single global
attendance threshold, in-app-only notifications, no refresh-token rotation).
The login rate limiter (SPEC 16) is process-local in-memory state — correct
for a single-process deployment, but a multi-worker production deployment
would need a shared store (e.g. Redis) for the same guarantee across
workers.

## Documentation Index

- [`docs/sdd/`](docs/sdd/) — one spec file per development phase, SPEC 00–18.
- [`docs/architecture.md`](docs/architecture.md)
- [`docs/data-model.md`](docs/data-model.md)
- [`docs/api-contract.md`](docs/api-contract.md)
- [`docs/testing-strategy.md`](docs/testing-strategy.md)
- [`docs/traceability-matrix.md`](docs/traceability-matrix.md)
