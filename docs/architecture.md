# Architecture

## Overview

```text
                    ┌──────────────────────┐
                    │   React + TS (Vite)  │
                    │  frontend/src         │
                    └──────────┬───────────┘
                               │ HTTPS/JSON (JWT bearer)
                    ┌──────────▼───────────┐
                    │       FastAPI          │
                    │  Router → Service →    │
                    │  Repository → SQLAlchemy│
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  SQLite (dev/test) /   │
                    │  PostgreSQL (prod)     │
                    └───────────────────────┘

                    ┌───────────────────────┐
                    │  Google Gemini API     │
                    │  (server-side only)    │
                    └───────────────────────┘
```

## Backend layering

```text
backend/app/
  main.py              # FastAPI app factory, middleware, router registration
  core/
    config.py          # Settings (pydantic-settings), reads .env
    security.py         # password hashing, JWT encode/decode
    database.py          # SQLAlchemy engine/session
    logging.py            # logging config
    exceptions.py          # domain exceptions -> HTTP mapping
    permissions.py          # role/permission constants + dependency factories
  models/                 # SQLAlchemy ORM models (one module per aggregate)
  schemas/                # Pydantic request/response models
  repositories/           # DB query layer, one per aggregate
  services/               # business logic, orchestrates repositories
  api/                    # FastAPI routers, thin — validate + call service
  tests/                  # pytest, mirrors api/service structure
alembic/                  # migrations
```

Rule: **routers never touch the DB directly** and **services never see
`Request`/`Response` objects** — this keeps business logic independently
testable from HTTP concerns.

## Frontend layering

```text
frontend/src/
  api/          # thin fetch wrappers per resource, typed
  services/     # TanStack Query hooks wrapping api/
  components/   # reusable: DataTable, Pagination, FilterBar, Modal,
                # ConfirmDialog, StatusBadge, AttendanceBadge, Chart,
                # EmptyState, LoadingState, ErrorState, Toast
  layouts/      # AppShell per role (nav differs by role)
  pages/        # route-level screens, composed from components
  routes/       # React Router route tree + role-guards
  hooks/        # useAuth, useRole, etc.
  types/        # shared TS types (mirrors backend Pydantic schemas)
  utils/        # formatting, date helpers
```

## Authentication & Authorization

- JWT bearer token, `sub` = user id, `role` claim(s) embedded, 60-minute
  expiry (see Assumption A-9 in `00-product-spec.md`).
- `get_current_user` FastAPI dependency decodes/validates the token.
- `require_role(*roles)` dependency factory gates endpoints; enforced
  **server-side only** — the frontend hides UI affordances as a UX nicety,
  never as the security boundary.
- Passwords hashed with bcrypt (`passlib[bcrypt]`).

## Database strategy

- SQLAlchemy models are the schema source of truth; Alembic manages
  migrations.
- Dev/test: SQLite file (`./dev.db`, `./test.db`), configured via
  `DATABASE_URL`.
- Production: PostgreSQL via the same `DATABASE_URL` — schema avoids
  dialect-specific types (no ARRAY/JSONB-only operators) so both engines work
  unmodified. See Assumption A-1.
- Every FK column is indexed; composite indexes added where list/report
  filters require them (documented per-spec).

## Error handling contract

All error responses follow:

```json
{
  "success": false,
  "error": { "code": "ATTENDANCE_SESSION_NOT_FOUND", "message": "..." }
}
```

Domain exceptions (`backend/app/core/exceptions.py`) map to HTTP status +
stable `code` string; a global exception handler ensures stack traces/secrets
never leak in responses (see `16-security-spec.md`). Pydantic request-body
validation failures (`422`) use the same envelope with `code:
"VALIDATION_ERROR"` and an additional `error.details` array carrying
FastAPI's normal per-field error list (`loc`/`msg`/`type`), so the frontend
can still show field-specific messages.

## AI integration

Gemini is called only from `services/gemini_insight_service.py`, which:
1. Pulls the `GEMINI_API_KEY` from environment (never hardcoded, never
   returned to the client).
2. Builds a prompt from **already-computed** structured attendance data.
3. Applies a timeout and catches provider errors, returning an advisory
   "insight unavailable" response rather than failing the request.
4. Is fully mockable in tests (the HTTP client is injected).

## Testing strategy summary

See `testing-strategy.md` for the full pyramid; summarized here:
Unit (services, pure calculation functions) → Integration (FastAPI
`TestClient` against a real SQLite test DB, one per test function) →
Frontend component tests (Vitest + RTL) → E2E (Playwright) for the six
required workflows.
