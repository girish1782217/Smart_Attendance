# SPEC 16 — Security Hardening

## Status
COMPLETE

## Objective
A security review across the areas the brief names (§16), plus concrete new
controls for the gaps the review finds: login brute-force protection,
standard security response headers, and a startup guard against running
production with the insecure default JWT secret.

## Review Findings (already satisfied by earlier specs — cited, not re-done)
- **Authentication**: bcrypt password hashing, JWT with expiry + server-side
  revocation list (SPEC 02). Verified: `hashed_password` never appears in
  any response schema (`test_auth.py::test_protected_endpoint_with_valid_token_returns_user_profile`).
- **Authorization**: every mutating endpoint since SPEC 03 is gated by
  `require_role`; every "my own data" endpoint since SPEC 07 resolves
  identity server-side via `scoping.py`, never trusting a client-supplied
  id for anything but ADMIN. Verified across ~120 existing authorization
  tests.
- **SQL injection**: 100% SQLAlchemy ORM query construction — grep-verified
  zero instances of raw SQL string interpolation anywhere in `app/`
  (`grep -rn "f\".*SELECT\|execute(f\"" app/` → no matches). Parameters
  (including search strings) are always bound via the ORM, never
  string-formatted into a query.
- **Input validation**: every request body is a Pydantic schema with
  explicit fields (no `**kwargs` passthrough anywhere) — mass assignment is
  structurally not possible.
- **API error leakage**: the global exception handler (SPEC 01) converts
  any unhandled exception to a generic `500` envelope; verified no stack
  trace or internal detail leaks (`test_error_handling.py`).
- **Secret handling**: `GEMINI_API_KEY`/`JWT_SECRET`/`DATABASE_URL` are
  `.env`-only, gitignored, never referenced in any Pydantic response
  schema, and the Gemini client (SPEC 15) never echoes the key back.
- **CSRF**: not applicable to this API's auth model — bearer tokens must be
  explicitly attached by client JavaScript (no ambient cookie credential a
  browser would auto-attach cross-site), which is the standard mitigation
  REST APIs rely on instead of CSRF tokens.
- **CORS**: origins are explicitly configured (`CORS_ORIGINS`, default
  `http://localhost:5173`) — not a wildcard `*`.

## Gaps Found & Addressed
1. **No brute-force protection on login.** Added a per-email in-memory
   rate limiter (`app/services/rate_limit_service.py`): 5 failed attempts
   within a 15-minute window → `429 RATE_LIMITED`; a successful login
   clears the counter. **Documented limitation**: in-memory, per-process —
   correct for a single-process deployment (this project's scope); a
   multi-worker production deployment would need a shared store (Redis) for
   the same guarantee across workers.
2. **No standard security response headers.** Added middleware setting
   `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
   `Referrer-Policy: strict-origin-when-cross-origin` on every response.
3. **No startup guard against the insecure default `JWT_SECRET` in
   production.** `config.py` gains `validate_production_settings(settings)`,
   called at `create_app()` startup — raises `RuntimeError` immediately if
   `ENVIRONMENT=production` and `JWT_SECRET` is still the insecure
   placeholder, rather than silently running an insecure deployment.

## Requirements
- R1: Login rate limiting: 5 failed attempts per email / 15 minutes → `429`;
  reset on success.
- R2: Security headers present on every response.
- R3: Production startup fails fast with a clear error if `JWT_SECRET` is
  the insecure default.
- R4: A regression test proving SQL-injection-style input in a search
  parameter is treated as a literal string, not executed.

## Acceptance Criteria
- AC1: 5 consecutive failed logins for one email → the 6th attempt (even
  with the *correct* password) → `429 RATE_LIMITED`.
- AC2: A successful login clears the counter — a prior near-miss streak
  doesn't carry over indefinitely.
- AC3: `GET /health` response includes all 3 security headers.
- AC4: `validate_production_settings` raises for the default secret in
  production, and does not raise for a custom secret or a non-production
  environment.
- AC5: Searching with a payload like `"'; DROP TABLE students; --"` returns
  a normal (empty) result set, not an error — proving parameterization.

## Technical Design
- `app/core/exceptions.py`: add `TooManyRequestsError` (429).
- `app/services/rate_limit_service.py` (new).
- `app/services/auth_service.py`: wire rate-limit check/register/clear into
  `authenticate`.
- `app/core/config.py`: add `validate_production_settings`.
- `app/main.py`: call it at startup; add the security-headers middleware.
- `backend/tests/conftest.py`: autouse fixture resetting the rate limiter
  between tests (it's process-global in-memory state, so it must not leak
  across the test suite).

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_security.py`.

## Test Results
8 new tests in `backend/tests/test_security.py`, all passed on first run.
Also verified via direct grep (`grep -rn "execute(f\"..." app/`) that zero
raw SQL string interpolation exists anywhere in the codebase before writing
the finding above, rather than asserting it without checking.

## Defects Found
None — all 8 new tests passed on first implementation.

## Fixes Applied
N/A.

## Regression Results
Full backend suite (`pytest -q`, from `backend/`): **166 passed** (158 from
SPEC 01–15 + 8 new). No regressions. In particular, adding a
`rate_limit_service` check into `auth_service.authenticate` (called by
every login across the entire suite) required the new autouse
`_reset_rate_limiter` fixture in `conftest.py` to avoid cross-test
pollution — verified by the fact that SPEC 02's `test_auth.py` (10 tests,
several logging in with the same fixture-generated credentials across
functions) still passes unmodified.

## Acceptance Verification
- AC1 ✅ 5 failed attempts then a 6th attempt with the *correct* password
  still returns `429 RATE_LIMITED` (proves the limiter blocks by attempt
  count, not just repeated failures).
- AC2 ✅ a successful login mid-stream resets the counter; a fresh run of 3
  more failures afterward stays at `401`, not `429`.
- AC3 ✅ `GET /health` carries all 3 security headers.
- AC4 ✅ `validate_production_settings` raises only for
  `production` + default secret; a custom secret or non-production
  environment (even with the default secret — a normal dev setup) never
  raises.
- AC5 ✅ a `'; DROP TABLE departments; --` search payload returns a normal
  empty result (not a `500`), and a follow-up ordinary search still finds
  the seeded department — proving the table was never touched.

All acceptance criteria met. All purely-backend specs (01–16) are now
complete; SPEC 17 (UX Polish) and SPEC 18 (Final Acceptance) require the
frontend, which begins next per the user's explicit prioritization
("finish all backend specs first, then build the frontend").

## Final Status
COMPLETE
