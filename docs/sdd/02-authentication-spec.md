# SPEC 02 — Authentication

## Status
COMPLETE

## Objective
Implement credential-based login, password hashing, JWT issuance/validation,
logout (server-side revocation), and a current-user endpoint, with
authentication middleware other specs can depend on.

## Requirements
- R1: `users` table: identity + hashed credentials only (no role data yet —
  that is SPEC 03's concern; keeps this spec's tests focused purely on auth
  mechanics, matching the brief's own SPEC-02 test list).
- R2: Passwords hashed with bcrypt; plaintext passwords are never stored or
  logged.
- R3: `POST /api/v1/auth/login` — validates credentials, returns a JWT
  access token. Failure (unknown email OR wrong password) returns the same
  generic `401 INVALID_CREDENTIALS` to avoid user enumeration.
- R4: `GET /api/v1/auth/me` — returns the authenticated user's profile;
  requires a valid bearer token.
- R5: `POST /api/v1/auth/logout` — revokes the presented token so it can no
  longer authenticate (server-side revocation via a `revoked_tokens` table
  keyed by JWT `jti`, since JWTs are otherwise stateless and can't be
  "deleted" client-side alone — see Assumption below).
- R6: `get_current_user` FastAPI dependency: decodes/validates the bearer
  token, rejects missing/malformed/expired/revoked tokens, loads the user,
  rejects inactive users.
- R7: Access tokens expire after `JWT_EXPIRE_MINUTES` (default 60 — see
  Assumption A-9 in `00-product-spec.md`).

## Assumption (spec-local)
**A-2-1 (Logout for stateless JWT)**: A JWT can't be invalidated purely
client-side. `POST /auth/logout` inserts the token's `jti` into a
`revoked_tokens` table (jti, expires_at); `get_current_user` rejects any
token whose `jti` is revoked. Expired rows are opportunistically deleted on
each revoke so the table doesn't grow unbounded. No refresh tokens exist in
v1 (Assumption A-9), so this fully covers logout.

## Acceptance Criteria
- AC1: Valid login (correct email + password) → `200` + JWT.
- AC2: Invalid password → `401 INVALID_CREDENTIALS`.
- AC3: Unknown email → `401 INVALID_CREDENTIALS` (identical to AC2 — no
  enumeration).
- AC4: Expired token on a protected endpoint → `401 TOKEN_EXPIRED`.
- AC5: Missing token on a protected endpoint → `401 MISSING_TOKEN`.
- AC6: Malformed/invalid-signature token → `401 INVALID_TOKEN`.
- AC7: Valid token on a protected endpoint (`/auth/me`) → `200` + correct
  user profile.
- AC8: Logout revokes the token; subsequent use of the same token →
  `401 TOKEN_REVOKED`.
- AC9: Inactive user cannot authenticate even with correct credentials.
- AC10: Password hash is never present in any API response.

## Technical Design
- `app/models/user.py` — `User` ORM model.
- `app/models/revoked_token.py` — `RevokedToken` ORM model.
- `app/core/security.py` — `hash_password`, `verify_password`,
  `create_access_token`, `decode_access_token`.
- `app/repositories/user_repository.py`, `app/repositories/token_repository.py`.
- `app/services/auth_service.py` — `authenticate`, `create_user`, `logout`.
- `app/api/deps.py` — `get_current_user` dependency (consumed by every future
  protected router, and extended by SPEC 03 with `require_role`).
- `app/api/v1/auth.py` — the three endpoints, registered on `api_v1_router`.
- `app/schemas/auth.py`, `app/schemas/user.py`.
- Alembic migration `0001_create_users_and_revoked_tokens`.

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_auth.py` — covers AC1–AC10.

## Test Results

```
tests/test_auth.py::test_login_with_valid_credentials_returns_token PASSED
tests/test_auth.py::test_login_with_wrong_password_returns_invalid_credentials PASSED
tests/test_auth.py::test_login_with_unknown_email_returns_same_invalid_credentials_error PASSED
tests/test_auth.py::test_login_with_inactive_user_is_rejected PASSED
tests/test_auth.py::test_protected_endpoint_without_token_returns_missing_token PASSED
tests/test_auth.py::test_protected_endpoint_with_malformed_token_returns_invalid_token PASSED
tests/test_auth.py::test_protected_endpoint_with_expired_token_returns_token_expired PASSED
tests/test_auth.py::test_protected_endpoint_with_valid_token_returns_user_profile PASSED
tests/test_auth.py::test_logout_revokes_token_so_it_can_no_longer_be_used PASSED
tests/test_auth.py::test_logout_without_token_returns_missing_token PASSED
10 passed
```

Also verified manually: `alembic revision --autogenerate` produced the
expected `create_table` operations for `users`/`revoked_tokens`, and
`alembic upgrade head` applied cleanly against a real SQLite file
(confirmed both tables + `alembic_version` exist afterward).

## Defects Found
None — all tests passed on first implementation.

## Fixes Applied
N/A.

## Regression Results
Full backend suite (`pytest -v`, from `backend/`): **14 passed** (4 from
SPEC 01 + 10 new). No regressions.

## Acceptance Verification
- AC1–AC3 ✅ valid login, wrong password, unknown email — the latter two
  return an identical `401 INVALID_CREDENTIALS` (no enumeration).
- AC4–AC6 ✅ expired/missing/malformed tokens return distinct codes
  (`TOKEN_EXPIRED` / `MISSING_TOKEN` / `INVALID_TOKEN`).
- AC7 ✅ `/auth/me` returns the correct profile for a valid token.
- AC8 ✅ logout revokes the token; reuse returns `401 TOKEN_REVOKED`.
- AC9 ✅ inactive user cannot authenticate (same generic error as AC2/AC3).
- AC10 ✅ `test_protected_endpoint_with_valid_token_returns_user_profile`
  asserts neither `password` nor `hashed_password` appears in the response.

All acceptance criteria met. Proceeding to SPEC 03 (RBAC).

## Final Status
COMPLETE
