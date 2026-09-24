# SPEC 01 — Project Foundation

## Status
COMPLETE

## Objective
Stand up the project skeleton (backend + frontend), environment
configuration, database connectivity, logging, consistent error handling,
and base test infrastructure, proven by a working health endpoint.

## Requirements
- R1: Backend project structure per `architecture.md` layering.
- R2: Frontend project structure (React + TS + Vite) per `architecture.md`.
- R3: `DATABASE_URL`-driven SQLAlchemy engine/session (SQLite dev/test,
  Postgres-ready — Assumption A-1).
- R4: Centralized settings via `.env` / `.env.example` (no secrets
  committed).
- R5: Structured logging.
- R6: Consistent JSON error envelope for domain + unhandled exceptions,
  never leaking internals.
- R7: `GET /health` returns 200 with a JSON body confirming the service is up.
- R8: Backend test harness: pytest + isolated per-test SQLite DB + TestClient
  fixture.
- R9: Frontend test harness: Vitest + React Testing Library.
- R10: Frontend renders a minimal shell and can reach the backend `/health`
  endpoint (proves the two halves are wired together).

## Acceptance Criteria
- AC1: `GET /health` returns `200` with `{"success": true, "status": "ok", ...}`.
- AC2: `pytest` passes with ≥1 real test exercising the health endpoint via
  `TestClient`.
- AC3: `npm run build` succeeds for the frontend.
- AC4: `npm test` passes with ≥1 real frontend test.
- AC5: No secret values are committed (`.env` is gitignored; only
  `.env.example` with empty values is committed).
- AC6: An unhandled backend exception returns the standard error envelope,
  not a raw traceback.

## Technical Design
See `docs/architecture.md` (layering, error contract, DB strategy) — SPEC 01
implements the skeleton described there with no domain logic yet.

Backend stack: FastAPI, SQLAlchemy 2.x, Alembic, pydantic-settings, bcrypt,
PyJWT (JWT wiring lands functionally in SPEC 02; the dependency is installed
now so the environment is fixed once).

Frontend stack: React 18 + TypeScript + Vite, Tailwind CSS v4, React Router,
TanStack Query, Vitest + React Testing Library.

## Implementation
- `backend/app/core/config.py` — `Settings` (pydantic-settings), `.env`-driven.
- `backend/app/core/database.py` — engine/session factory, `get_db` dependency.
- `backend/app/core/logging_config.py` — logging setup.
- `backend/app/core/exceptions.py` — `AppError` hierarchy + envelope.
- `backend/app/main.py` — app factory, CORS, exception handlers, router
  registration.
- `backend/app/api/health.py` — `GET /health`.
- `backend/tests/conftest.py` — `db_session` + `client` fixtures (isolated
  in-memory SQLite per test).
- `backend/tests/test_health.py`.
- `frontend/` — Vite React-TS scaffold, Tailwind v4, router/query providers,
  a minimal `HealthStatus` component + page proving connectivity, plus its
  Vitest test.

## Tests
- `backend/tests/test_health.py::test_health_check`
- `frontend/src/components/__tests__/HealthStatus.test.tsx`

## Test Results

Backend (`pytest -v`, from `backend/`):
```
tests/test_error_handling.py::test_app_error_returns_standard_envelope PASSED
tests/test_error_handling.py::test_unhandled_error_returns_generic_envelope_without_leaking_details PASSED
tests/test_health.py::test_health_check_returns_ok PASSED
tests/test_health.py::test_unknown_route_returns_404 PASSED
4 passed in 0.09s
```

Also verified the app boots for real (not just via `TestClient`): started
`uvicorn app.main:app` on port 8123 and confirmed `curl /health` returned
`200 {"success":true,"status":"ok","service":"smart-attendance-backend"}`.

Frontend (`npm test`, from `frontend/`):
```
Test Files  1 passed (1)
     Tests  2 passed (2)
```
`npm run build` succeeded (produces `dist/`). `npm run lint` (oxlint) passed
with zero findings.

## Defects Found
1. `ApiError` used TypeScript constructor-parameter-property shorthand
   (`public readonly status: number`), which the template's
   `erasableSyntaxOnly` tsconfig option rejects (that syntax emits runtime
   code, so it isn't purely erasable) — surfaced only at `tsc -b` build time,
   not at test time.
2. `vite.config.ts`'s `/// <reference types="vitest/config" />` triple-slash
   directive was placed after other import statements; TypeScript only
   honors such directives at the very top of the file, so the `test` key in
   `defineConfig` failed to type-check.

## Fixes Applied
1. Rewrote `ApiError` (`frontend/src/api/client.ts`) with explicit field
   declarations and constructor-body assignment instead of parameter
   properties.
2. Moved the triple-slash reference to the first line of
   `frontend/vite.config.ts`, before all imports.

Both fixes verified by re-running `npm run build` (success) and `npm test`
(still 2/2 passing).

## Regression Results
N/A (first implemented spec — nothing prior to regress against). Full suite
counts above stand as the baseline for SPEC 02's regression run.

## Acceptance Verification
- AC1 ✅ `GET /health` → 200, correct body (verified via `TestClient` and a
  real running server).
- AC2 ✅ `pytest` passes, 4 tests, including a direct `TestClient` hit on
  `/health`.
- AC3 ✅ `npm run build` succeeds.
- AC4 ✅ `npm test` passes, 2 tests covering healthy and error states.
- AC5 ✅ Only `.env.example` (backend and frontend) is committed; real
  `.env` files are gitignored and contain no committed secrets.
- AC6 ✅ `test_unhandled_error_returns_generic_envelope_without_leaking_details`
  proves an unhandled `RuntimeError` returns the generic envelope with no
  trace of the original exception message.

All acceptance criteria met. Proceeding to SPEC 02 (Authentication).

## Final Status
COMPLETE
