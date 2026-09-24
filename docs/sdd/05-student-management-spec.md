# SPEC 05 — Student Management

## Status
COMPLETE

## Objective
Implement the Student entity: a 1:1 link to a login-capable `User` (role
STUDENT) plus academic enrollment (current Section), with CRUD, duplicate
prevention, search/filter/pagination, and authorization.

## Design
- `Student` (`id`, `user_id` FK→`users.id` unique, `roll_number` unique,
  `section_id` FK→`sections.id`, `phone` nullable, + timestamp/soft-delete
  mixins). No `full_name`/`email` duplicated here — those live on the linked
  `User`; responses join them in.
- Creating a Student **atomically** creates its backing `User` (STUDENT
  role) in the same DB transaction (`db.flush()` to obtain `user.id` before
  inserting the `Student` row, single `db.commit()`) — so a failure partway
  through never leaves an orphaned login-only user or a profile-less
  student.
- Deactivating a Student also deactivates its linked `User`
  (`user.is_active = False`) — a removed/graduated student shouldn't retain
  login access either.
- No `class_id`/`department_id` on `Student` directly — those are derivable
  through `section → class → program → department`. A student's "current"
  section is reassigned via update as they progress (Assumption A-6: exactly
  one (class, section) at a time; no historical enrollment table in v1).
- Scope note: this spec's `GET /students` supports search + `section_id`
  filter + pagination only. Department/class/program-level rollups belong to
  SPEC 11 (low attendance) / SPEC 12 (reports), which need aggregated
  queries shaped differently anyway — adding that filtering chain here would
  duplicate logic those specs build properly.

## Requirements
- R1: Create a Student = create `User` (STUDENT role) + `Student` profile,
  atomically.
- R2: Duplicate prevention on `email` (shared with SPEC 02/03's `users`
  table) and `roll_number`.
- R3: `section_id` must reference an existing Section.
- R4: List: search (roll_number, user full_name, user email — case
  insensitive), `section_id` filter, pagination. Uses `joinedload` on `user`
  to avoid N+1 (a list of up to 100 rows must not issue 100 extra queries).
- R5: Update: full_name (proxied to `User`), phone, section_id (with FK
  re-validation), is_active.
- R6: Authorization — list/get: ADMIN + FACULTY (faculty need to see student
  info for their classes; students do not browse other students' profiles).
  Mutations: ADMIN only.

## Acceptance Criteria
- AC1: Admin creates a student; both a `users` row (STUDENT role) and a
  `students` row exist and are correctly linked.
- AC2: Duplicate email → `409 USER_EMAIL_EXISTS`; duplicate roll number →
  `409 STUDENT_ROLL_NUMBER_DUPLICATE`.
- AC3: Non-existent `section_id` → `404 SECTION_NOT_FOUND`.
- AC4: Student role cannot list/get/create/update any student record
  (`403`); Faculty can list/get but not create/update/deactivate (`403`).
- AC5: Search matches on roll number, name, or email.
- AC6: Deactivating a student also deactivates their login (`user.is_active
  == False`); a subsequent login attempt fails.
- AC7: Updating `section_id` re-validates the new section exists.

## Technical Design
- `app/models/student.py`.
- `app/repositories/student_repository.py` (custom — joins `User`, not a
  plain `CRUDBase` user, since search spans two tables).
- `app/services/student_service.py`.
- `app/schemas/student.py`.
- `app/api/v1/students.py`.
- Alembic migration `0004_create_students`.

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_students.py`.

## Test Results
11 new tests in `backend/tests/test_students.py`, all passed, including a
round-trip proof that the atomically-created backing user can actually log
in (AC1) and that deactivation disables that login (AC6). Verified manually:
migration applies cleanly to a real SQLite file.

## Defects Found
None — all tests passed on first implementation.

## Fixes Applied
N/A.

## Regression Results
Full backend suite (`pytest -v`, from `backend/`): **59 passed** (48 from
SPEC 01–04 + 11 new). No regressions.

## Acceptance Verification
- AC1 ✅ `test_admin_can_create_student_with_backing_user` creates a student
  and then successfully logs in as that exact account.
- AC2 ✅ duplicate email → `409 USER_EMAIL_EXISTS`; duplicate roll number →
  `409 STUDENT_ROLL_NUMBER_DUPLICATE`.
- AC3 ✅ non-existent `section_id` → `404 SECTION_NOT_FOUND` (both on create
  and on update).
- AC4 ✅ STUDENT role gets `403` on `GET /students`; FACULTY can list/get but
  gets `403` on `POST /students`.
- AC5 ✅ search matches roll number, name, and email independently.
- AC6 ✅ after deactivation, a login attempt with the student's original
  credentials returns `401 INVALID_CREDENTIALS`.
- AC7 ✅ `PATCH` with an invalid `section_id` returns `404` before any write.

All acceptance criteria met. Proceeding to SPEC 06 (Faculty Management).

## Final Status
COMPLETE
