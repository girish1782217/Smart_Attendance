# SPEC 08 — Attendance Recording

## Status
COMPLETE

## Objective
Implement `AttendanceRecord` (PRESENT/ABSENT/LATE/EXCUSED per student per
session), bulk save (idempotent upsert), submit/finalize, and the
deterministic attendance-percentage calculation formalized in
`00-product-spec.md` Assumption A-2.

## Design
- `AttendanceRecord`: `session_id`, `student_id`, `status`, `recorded_by_user_id`,
  `recorded_at` (refreshed on every write), `created_at`. Unique on
  `(session_id, student_id)` (BR-1) — a plain `UniqueConstraint` is correct
  here (unlike `FacultyAssignment` in SPEC 06) because a record is never
  reactivated/soft-deleted; a wrong mark is corrected in place via SPEC 09's
  workflow, which updates this same row's `status`, not a new one.
- **Save vs. submit are separate actions**: `PUT /{session_id}/records` is
  an idempotent bulk upsert (create-if-absent, update-if-present) usable
  any number of times while the session is `SCHEDULED` — this is both
  "save" and "bulk marking" from the brief, unified into one endpoint since
  they're the same operation at different points in a marking session.
  `POST /{session_id}/submit` is the one-way `SCHEDULED → SUBMITTED`
  transition (BR-3): once submitted, `PUT /records` is rejected
  (`409 SESSION_ALREADY_SUBMITTED`) — changes must go through SPEC 09's
  correction workflow instead.
- **Complete-roster rule**: `submit` is rejected
  (`409 INCOMPLETE_ROSTER`) unless every currently-active student in the
  session's section already has a record. This gives concrete meaning to
  the brief's "Complete roster" test case: you can't finalize attendance
  with unmarked students.
- **Roster validation on save**: every `student_id` in a bulk-mark payload
  must be an active member of the session's section (same roster query
  SPEC 07 exposes at `.../roster`) — otherwise `404 STUDENT_NOT_IN_ROSTER`.
  One check covers "doesn't exist," "wrong section," and "inactive" — the
  brief's "Invalid student" case doesn't need finer-grained codes.
- **Ownership**: reuses SPEC 07's `ensure_faculty_can_access` +
  `scoping.resolve_faculty_filter` — a FACULTY caller can only mark/submit/
  view records for their own sessions.
- **Attendance percentage formula** (Assumption A-2, now implemented as a
  pure, independently-unit-tested function,
  `app/services/attendance_calculations.py::calculate_attendance_percentage`):
  `EXCUSED` is removed from both numerator and denominator; `LATE` counts as
  a full present-equivalent; zero applicable sessions returns `None`
  ("no data"), never `0` or `100`. This function is the single source of
  truth reused by SPEC 10/11/12 — attendance % is never computed ad hoc or
  by the frontend/AI.

## Requirements
- R1: `PUT /attendance-sessions/{id}/records` — bulk upsert, all 4 statuses,
  rejects duplicate `student_id` within one request payload (`422`),
  rejects any `student_id` not on the active roster (`404`), rejects
  writing to an already-`SUBMITTED` session (`409`).
- R2: `POST /attendance-sessions/{id}/submit` — one-way transition, requires
  a complete roster, rejects double-submit.
- R3: `GET /attendance-sessions/{id}/records` — current marks, joined with
  student name/roll number.
- R4: `calculate_attendance_percentage` is a pure function, unit-tested
  independently of any HTTP/DB layer.
- R5: Authorization: ADMIN or the owning FACULTY only; STUDENT is fully
  excluded (BR-5 — students never write attendance).

## Acceptance Criteria
- AC1: Each of PRESENT/ABSENT/LATE/EXCUSED can be recorded and re-saved
  (upsert) before submission.
- AC2: A `student_id` not on the session's active roster → `404
  STUDENT_NOT_IN_ROSTER`.
- AC3: A FACULTY caller who doesn't own the session → `403` (reusing SPEC
  07's ownership check).
- AC4: Two entries for the same `student_id` in one bulk request → `422`.
- AC5: Submitting with any unmarked active student → `409 INCOMPLETE_ROSTER`;
  submitting a fully-marked session → `200`, session `status: SUBMITTED`.
- AC6: `PUT /records` on an already-`SUBMITTED` session → `409
  SESSION_ALREADY_SUBMITTED`.
- AC7: `calculate_attendance_percentage` unit tests cover: all present
  (100%), all absent (0%), mixed, all excused (`None`), empty (`None`), and
  that `LATE` counts as present-equivalent.
- AC8: STUDENT role → `403` on every endpoint in this spec.

## Technical Design
- `app/models/attendance_record.py` (+ `AttendanceStatus` enum).
- `app/repositories/attendance_record_repository.py`.
- `app/services/attendance_calculations.py` (pure function).
- `app/services/attendance_record_service.py` (bulk-mark, submit, list —
  business rules, calls the calculation module where relevant).
- `app/schemas/attendance_record.py`.
- New endpoints added to the existing `app/api/v1/attendance_sessions.py`
  router (session-scoped sub-resources, not a separate top-level router).
- Alembic migration `0007_create_attendance_records`.

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_attendance_recording.py`,
`backend/tests/test_attendance_calculations.py`.

## Test Results
8 unit tests in `test_attendance_calculations.py` (pure function, no
DB/HTTP) + 10 integration tests in `test_attendance_recording.py`. All
passed on first run. Verified manually: migration applies cleanly to a real
SQLite file.

## Defects Found
None — all 18 new tests passed on first implementation.

## Fixes Applied
N/A.

## Regression Results
Full backend suite (`pytest -v`, from `backend/`): **101 passed** (83 from
SPEC 01–07 + 18 new). No regressions.

## Acceptance Verification
- AC1 ✅ all 4 statuses recorded in one bulk call; re-saving upserts (verified
  the row count stays at 1, not 2, after a second save for the same
  student).
- AC2 ✅ a nonexistent `student_id` → `404 STUDENT_NOT_IN_ROSTER`.
- AC3 ✅ a faculty member who doesn't own the session → `403`.
- AC4 ✅ the same `student_id` twice in one request → `422`.
- AC5 ✅ submit with one of two students unmarked → `409 INCOMPLETE_ROSTER`;
  submit with both marked → `200`, `status: SUBMITTED`.
- AC6 ✅ `PUT /records` after submission → `409 SESSION_ALREADY_SUBMITTED`
  (same code as double-submit, reused deliberately — both describe "this
  session is already finalized").
- AC7 ✅ 8 dedicated unit tests: all-present (100%), all-absent (0%), mixed
  (50%), LATE-as-present (100%), EXCUSED removed from both numerator and
  denominator, all-EXCUSED → `None`, empty → `None`, rounding to 2 decimals.
- AC8 ✅ STUDENT → `403` on bulk-mark, list-records, and submit.

All acceptance criteria met. Proceeding to SPEC 09 (Attendance Correction).

## Final Status
COMPLETE
