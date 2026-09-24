# SPEC 06 — Faculty Management

## Status
COMPLETE

## Objective
Implement the Faculty entity (mirrors Student's design: 1:1 link to a
login-capable `User` with role FACULTY) plus `FacultyAssignment`, the join
that says "this faculty member teaches this subject to this section in this
semester" — the record SPEC 07's attendance sessions validate against
(Assumption A/business rule from `00-product-spec.md`: "a faculty member may
only create sessions for (section, subject) pairs they are assigned to").

## Design
- `Faculty` (`id`, `user_id` FK→`users.id` unique, `employee_id` unique,
  `department_id` FK→`departments.id`, `phone` nullable, + mixins). Same
  atomic create-user-and-profile pattern as `Student` (SPEC 05).
- `FacultyAssignment` (`id`, `faculty_id`, `subject_id`, `section_id`,
  `semester_id`, + timestamps + `is_active`). Unique on
  `(faculty_id, subject_id, section_id, semester_id)` — the same assignment
  can't be created twice, but a faculty member can teach multiple
  subjects/sections, and a subject/section can (in principle) rotate
  faculty across semesters.
- Deactivating a Faculty also deactivates their `User` login, mirroring
  Student.

## Requirements
- R1: Create Faculty = create `User` (FACULTY role) + `Faculty` profile,
  atomically.
- R2: Duplicate prevention on `email` and `employee_id`.
- R3: `department_id` must reference an existing Department.
- R4: List: search (employee_id, user full_name, user email),
  `department_id` filter, pagination.
- R5: `FacultyAssignment` CRUD (create/list/deactivate — no update; an
  assignment is either correct or replaced by a new one, mirroring a
  real timetable change): validates `faculty_id`/`subject_id`/`section_id`/
  `semester_id` all exist, rejects an exact-duplicate active assignment.
- R6: Authorization — Faculty CRUD: list/get ADMIN+FACULTY, mutate ADMIN
  only (same rationale as Student). `FacultyAssignment`: ADMIN only for
  create/deactivate; list open to ADMIN+FACULTY. **Design refinement made
  during implementation**: rather than a client-toggleable `?mine=true`
  flag (which would let a FACULTY caller choose `mine=false` and attempt to
  browse everyone), a FACULTY-role caller's `faculty_id` filter is *always*
  overridden server-side to their own linked Faculty id — there is no way
  to see another faculty member's assignments by passing a different id.
  ADMIN callers may filter by any `faculty_id` or omit it entirely.

## Acceptance Criteria
- AC1: Admin creates a faculty member; `users` (FACULTY role) + `faculty`
  rows exist and are linked; the account can log in.
- AC2: Duplicate email → `409`; duplicate employee_id → `409
  FACULTY_EMPLOYEE_ID_DUPLICATE`.
- AC3: Non-existent `department_id` → `404 DEPARTMENT_NOT_FOUND`.
- AC4: STUDENT gets `403` on all faculty endpoints; FACULTY can list/get but
  not create/update/deactivate.
- AC5: Creating a `FacultyAssignment` validates all 4 foreign keys and
  rejects a non-existent one with a specific `*_NOT_FOUND` code.
- AC6: Creating an exact-duplicate active assignment → `409
  ASSIGNMENT_DUPLICATE`.
- AC7: A faculty member listing assignments always sees only their own,
  resolved from their own token — an explicit `faculty_id` query param is
  ignored, not merely validated, for a FACULTY-role caller. A FACULTY-role
  user with no linked Faculty profile (an edge case — e.g. provisioned
  directly via `POST /users` rather than `POST /faculty`) gets a clean `404
  FACULTY_PROFILE_NOT_FOUND` rather than an error or an empty list.
- AC8: Deactivating a Faculty also disables their login.

## Technical Design
- `app/models/faculty.py`, `app/models/faculty_assignment.py`.
- `app/repositories/faculty_repository.py` (custom, joins `User` — same
  reasoning as Student). `app/repositories/faculty_assignment_repository.py`.
- `app/services/faculty_service.py`, `app/services/faculty_assignment_service.py`.
- `app/schemas/faculty.py`, `app/schemas/faculty_assignment.py`.
- `app/api/v1/faculty.py`, `app/api/v1/faculty_assignments.py`.
- Alembic migration `0005_create_faculty_and_assignments`.

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_faculty.py`.

## Test Results
12 new tests in `backend/tests/test_faculty.py` covering Faculty CRUD +
FacultyAssignment lifecycle. All passed after the two fixes below. Verified
manually: migration applies cleanly to a real SQLite file, and the partial
unique index's actual DDL was inspected directly
(`CREATE UNIQUE INDEX uq_faculty_assignment_active ON faculty_assignments
(faculty_id, subject_id, section_id, semester_id) WHERE is_active = 1`).

## Defects Found
1. **Real defect, caught by a failing test.** `FacultyAssignment` initially
   used a blanket `UniqueConstraint` on
   `(faculty_id, subject_id, section_id, semester_id)`. The service layer's
   duplicate check (`get_active_duplicate`) correctly only looks at
   `is_active=True` rows, but the DB constraint applied to *all* rows
   regardless of `is_active` — so deactivating an assignment and then
   recreating the identical combination (a legitimate flow: undoing a
   mistaken deactivation) failed with a raw `sqlite3.IntegrityError` that
   surfaced as an unhandled `500`, not the intended `201`.
   `test_admin_can_deactivate_assignment` caught this immediately.
2. **Test bug, not an implementation bug.**
   `test_faculty_sees_only_own_assignments_regardless_of_query_param`
   originally used the generic `make_auth_headers([RoleName.FACULTY])`
   fixture to simulate "a second faculty member" — but that fixture only
   creates a bare `User` row with the FACULTY role, not a linked `Faculty`
   profile (which only `POST /api/v1/faculty` creates). The test got `404
   FACULTY_PROFILE_NOT_FOUND`, which is in fact the correct, intended
   response for that edge case — the test's setup was wrong, not the code.

## Fixes Applied
1. Replaced the blanket `UniqueConstraint` with a partial unique `Index`
   (`sqlite_where="is_active = 1"`, `postgresql_where="is_active = true"`),
   so uniqueness is enforced only among active rows — matching the service
   layer's own check exactly. Regenerated the migration from scratch (it had
   not been committed yet) rather than layering a correction migration on
   top.
2. Rewrote the test to create the second faculty member through the real
   `POST /api/v1/faculty` endpoint (so it has a genuine linked profile with
   zero assignments), and added a separate, explicit test
   (`test_faculty_role_with_no_linked_profile_gets_404_on_assignments`) for
   the no-linked-profile edge case, so that behavior is now intentionally
   documented and covered rather than accidentally triggered.

## Regression Results
Full backend suite (`pytest -v`, from `backend/`): **71 passed** (59 from
SPEC 01–05 + 12 new in `test_faculty.py`). No regressions.

## Acceptance Verification
- AC1 ✅ faculty created with backing user; login succeeds with those exact
  credentials.
- AC2 ✅ duplicate email → `409`; duplicate employee_id → `409
  FACULTY_EMPLOYEE_ID_DUPLICATE`.
- AC3 ✅ non-existent `department_id` → `404 DEPARTMENT_NOT_FOUND`.
- AC4 ✅ STUDENT → `403` on faculty endpoints; FACULTY can list/get, `403` on
  mutate.
- AC5 ✅ each of the 4 FK checks on `FacultyAssignment` creation returns its
  own `*_NOT_FOUND` code, verified for `FACULTY_NOT_FOUND`.
- AC6 ✅ duplicate *active* assignment → `409 ASSIGNMENT_DUPLICATE`; verified
  distinctly from the deactivate-then-recreate case, which now succeeds.
- AC7 ✅ a FACULTY caller's own assignment list ignores a spoofed
  `faculty_id`; the no-profile edge case returns a clean `404`.
- AC8 ✅ deactivating a Faculty disables their login (`401` on next login
  attempt).

All acceptance criteria met. Proceeding to SPEC 07 (Attendance Session
Management).

## Final Status
COMPLETE
