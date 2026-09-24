# SPEC 03 — RBAC

## Status
COMPLETE

## Objective
Add role-based authorization on top of SPEC 02's authentication: fixed
system roles, many-to-many user↔role assignment, and a reusable
`require_role(...)` dependency that every future protected endpoint uses.

## Requirements
- R1: Three fixed system roles — `ADMIN`, `FACULTY`, `STUDENT` — seeded via
  migration data (not scattered as magic strings in application code; see
  `app/core/roles.py::RoleName`).
- R2: `roles` table + `user_roles` many-to-many join table (a user may hold
  more than one role — Assumption A in `00-product-spec.md` §2).
- R3: `require_role(*roles)` FastAPI dependency factory — generic (accepts
  one or more allowed roles), reusable by every future router.
- R4: Roles are read from the database on every request (via the
  authenticated user's `roles` relationship), not cached in the JWT — so a
  role change takes effect immediately, without requiring re-login.
- R5: Admin-only user/role management endpoints: create a user with initial
  role(s), list users (paginated), replace a user's role set — this is the
  concrete "role assignment" surface the brief's SPEC-03 calls for, and
  doubles as the mechanism for provisioning faculty/student login accounts
  in later specs.
- R6: A shared pagination convention (`Page[T]` response envelope,
  `page`/`page_size` query params, default 25 / max 100) — introduced here
  because it's needed by `GET /users` and will be reused by every list
  endpoint from SPEC 04 onward.

## Simplification (documented, in-scope for v1)
The brief's §18 schema sketch lists a separate `permissions` table. No
requirement in this project calls for admin-editable, fine-grained
permissions (the three roles' capabilities are fixed and fully enumerated in
`00-product-spec.md` §2) — so a `permissions` table would be unused
infrastructure. `require_role` checks role membership directly. If granular
permissions become a real requirement later, `permissions` +
`role_permissions` can be added without changing the `roles`/`user_roles`
shape.

## Acceptance Criteria
- AC1: Admin can create a user and assign role(s) (`POST /api/v1/users`).
- AC2: Faculty gets `403 FORBIDDEN` calling the same admin-only endpoint.
- AC3: Student gets `403 FORBIDDEN` calling the same admin-only endpoint.
- AC4: An unauthenticated request gets `401` (not `403`) — proves the
  missing-token check still runs before the role check.
- AC5: Admin can list users with pagination (`GET /api/v1/users`).
- AC6: Admin can assign multiple roles to one user
  (`PUT /api/v1/users/{id}/roles`).
- AC7: Duplicate email on user creation → `409 USER_EMAIL_EXISTS`.
- AC8: Invalid role name is rejected at the schema layer (`422`) before it
  ever reaches the service.
- AC9: `require_role` genuinely supports "any of several roles" (not just a
  single role) — proven with a dedicated test independent of the users
  endpoints.

## Technical Design
- `app/core/roles.py` — `RoleName(str, Enum)`.
- `app/models/role.py` — `Role` model + `user_roles` association `Table`.
- `app/models/user.py` — add `roles` relationship.
- `app/repositories/role_repository.py`, additions to `user_repository.py`.
- `app/services/user_service.py` — `create_user_with_roles`, `list_users`,
  `set_user_roles`.
- `app/schemas/pagination.py` — `Page[T]`, `PaginationParams`.
- `app/schemas/user.py` — `UserWithRolesResponse`, `CreateUserRequest`,
  `AssignRolesRequest`.
- `app/api/deps.py` — `require_role(*roles)`.
- `app/api/v1/users.py` — the three endpoints.
- Alembic migration `0002_create_roles_and_user_roles` (creates both tables
  + seeds the 3 roles via `op.bulk_insert`).
- **Test infrastructure note**: `backend/tests/conftest.py`'s `db_session`
  fixture now seeds the 3 roles after `Base.metadata.create_all(...)`,
  because `create_all` builds schema only — it does not run the migration's
  data seed. Every future test that needs a role-bearing user relies on this
  fixture-level seeding.

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_rbac.py` — covers AC1–AC9.

## Test Results

```
tests/test_rbac.py::test_admin_can_create_user_and_assign_role PASSED
tests/test_rbac.py::test_faculty_cannot_create_user PASSED
tests/test_rbac.py::test_student_cannot_create_user PASSED
tests/test_rbac.py::test_unauthenticated_request_returns_401_not_403 PASSED
tests/test_rbac.py::test_admin_can_list_users_with_pagination PASSED
tests/test_rbac.py::test_admin_can_assign_multiple_roles PASSED
tests/test_rbac.py::test_create_user_with_duplicate_email_returns_conflict PASSED
tests/test_rbac.py::test_create_user_with_invalid_role_name_is_rejected_by_schema PASSED
tests/test_rbac.py::test_require_role_grants_access_to_any_of_several_allowed_roles PASSED
9 passed
```

Also verified manually: `alembic upgrade head` applied the roles/user_roles
migration cleanly to a real SQLite file, and a direct query confirmed the 3
seeded rows (`ADMIN`/`FACULTY`/`STUDENT`) with correct descriptions.

## Defects Found
1. Running `alembic revision --autogenerate` immediately failed with
   "Target database is not up to date" — the local `dev.db` from SPEC 02
   had been deleted (it's gitignored, correctly), so the fresh file Alembic
   created had no `alembic_version` row at all.

## Fixes Applied
1. Ran `alembic upgrade head` first (bringing the fresh `dev.db` to the
   SPEC 02 revision), then re-ran `--autogenerate`, which succeeded. Not a
   code defect — a reminder that `dev.db` is disposable/regeneratable state,
   not a fixture to preserve.

## Regression Results
Full backend suite (`pytest -v`, from `backend/`): **23 passed** (14 from
SPEC 01–02 + 9 new). No regressions.

## Acceptance Verification
- AC1 ✅ admin creates a user with an assigned role, `201` + correct body.
- AC2/AC3 ✅ faculty and student both get `403 FORBIDDEN` on the same
  endpoint.
- AC4 ✅ unauthenticated request gets `401 MISSING_TOKEN`, not `403` —
  confirms the auth check runs before the role check inside `require_role`
  (it depends on `get_current_user`).
- AC5 ✅ `GET /api/v1/users?page=1&page_size=2` returns exactly 2 of 4 total
  users with correct `page`/`page_size` echoed back.
- AC6 ✅ a user's role set can be replaced with two roles at once.
- AC7 ✅ duplicate email → `409 USER_EMAIL_EXISTS`.
- AC8 ✅ an invalid role name (`"SUPERUSER"`) is rejected at `422` by the
  Pydantic enum field, before the service layer ever runs.
- AC9 ✅ dedicated synthetic-route test proves `require_role(ADMIN, FACULTY)`
  admits a FACULTY user and rejects a STUDENT user.

All acceptance criteria met. Proceeding to SPEC 04 (Master Data).

## Final Status
COMPLETE
