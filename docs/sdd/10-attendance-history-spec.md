# SPEC 10 — Attendance History

## Status
COMPLETE

## Objective
Expose read-only attendance history from a student's perspective: overall +
per-subject percentage summary, and a paginated, filterable detail list —
both scoped correctly per role, and showing correction outcomes where a
record was ever corrected.

## Scope note: "Faculty session history" already exists
The brief's SPEC-10 test list mentions "Faculty session history," but that's
already fully covered by SPEC 07's `GET /attendance-sessions?faculty_id=&
from_date=&to_date=` (auto-scoped to the caller's own sessions). This spec
adds the two capabilities that genuinely didn't exist yet: **student-centric**
and **subject-centric** history with percentage calculations.

## Design
- **Two endpoints, not one**, because they have different shapes and
  different consumers: `GET /students/{id}/attendance-summary` (small,
  unpaginated — one row overall + one row per subject the student has any
  records in) and `GET /students/{id}/attendance-history` (paginated,
  filterable detail rows). A combined endpoint would force one pagination
  scheme onto two very different result sizes.
- **Percentage reuses SPEC 08's `calculate_attendance_percentage`
  unchanged** — computed in Python over the fetched records (not raw SQL
  aggregation). For a single student's own history (bounded to their actual
  session count, never thousands), this is simpler and equally correct;
  cross-student aggregation with real scale concerns is SPEC 11/12's
  problem, and will need a different (SQL-side) approach there.
- **Scoping**: STUDENT may only view their own (`403` otherwise). FACULTY's
  view is **filtered, not blocked** — they see only the records belonging to
  their own sessions for that student (so a different subject's faculty
  can't infer a student's attendance in a subject they don't teach); zero
  matching records just yields a valid, honest all-zero summary, not an
  error. ADMIN sees everything.
- **Correction visibility**: each history row includes `was_corrected` and,
  if true, a `correction` object (original/approved status, reason,
  decision reason, reviewer, decision time) — sourced from SPEC 09's
  `correction_requests`, batched in one query per page (not N+1).

## Requirements
- R1: `GET /students/{id}/attendance-summary` — overall counts/percentage +
  per-subject breakdown.
- R2: `GET /students/{id}/attendance-history` — paginated, filterable by
  `subject_id`/`from_date`/`to_date`, each row shows the *current* (possibly
  corrected) status plus correction detail if applicable.
- R3: Role scoping exactly as described above.

## Acceptance Criteria
- AC1: A student's summary matches manually-computed expected
  percentages for a scripted set of PRESENT/ABSENT/LATE/EXCUSED records
  (cross-checks SPEC 08's formula end-to-end through a real HTTP call).
- AC2: `from_date`/`to_date`/`subject_id` filters on the history endpoint
  each work correctly and independently.
- AC3: A record with an approved correction shows the corrected
  (current) status plus `was_corrected: true` and full correction detail;
  data before correction is never silently lost (`correction.original_status`
  is preserved even though `status` shows the corrected value).
- AC4: STUDENT viewing another student's summary/history → `403`.
- AC5: FACULTY viewing a student's summary sees only their own subject's
  records reflected in the counts — a record from a different faculty
  member's session for the same student does not appear or affect the
  percentage.
- AC6: A student with zero attendance records → `percentage: null` (not `0`
  or `100`), consistent with SPEC 08 Assumption A-2.

## Technical Design
- `app/repositories/attendance_history_repository.py`.
- `app/repositories/correction_repository.py`: add `list_approved_for_records`.
- `app/services/attendance_history_service.py`.
- `app/schemas/attendance_history.py`.
- `app/api/v1/attendance_history.py` (new router, path prefix `/students`).

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_attendance_history.py`.

## Test Results
8 new tests in `backend/tests/test_attendance_history.py`, covering summary
percentage math cross-checked by hand, filtering, correction visibility, and
role scoping (including the faculty-scoped-to-own-subject case, verified by
constructing a scenario where an unscoped view would show a different
percentage than the correctly-scoped one).

## Defects Found
1. **Test bug, not an implementation bug** (same pattern as SPEC 06/07's
   analogous cases). `test_student_cannot_view_another_students_history`
   used `make_auth_headers([RoleName.STUDENT])` to simulate "a different
   student," but that fixture only creates a bare `User` with the STUDENT
   role, not a linked `Student` profile. The endpoint correctly returned
   `404 STUDENT_PROFILE_NOT_FOUND` (there is no "own" history to compare
   against for a profile-less user) instead of the expected `403`.

## Fixes Applied
1. Rewrote the test to create a genuine second student via `POST
   /api/v1/students` and assert `403` when that real student tries to view
   the first student's history. Added a new, explicit test
   (`test_student_role_with_no_linked_profile_gets_404`) documenting the
   no-linked-profile edge case as intentional behavior, matching the
   pattern already established for `FACULTY_PROFILE_NOT_FOUND` in SPEC 06.

## Regression Results
Full backend suite (`pytest -v`, from `backend/`): **119 passed** (111 from
SPEC 01–09 + 8 new). No regressions.

## Acceptance Verification
- AC1 ✅ a 4-record, 2-subject scenario (75% overall, 50%/100% per subject)
  matches hand-computed expectations exactly.
- AC2 ✅ `subject_id` and `from_date`/`to_date` filters each independently
  narrow the history list correctly.
- AC3 ✅ after an approved correction, the history row shows the corrected
  `status` (`PRESENT`) while `correction.original_status` still reads
  `ABSENT` — nothing is silently lost.
- AC4 ✅ a genuine second student gets `403` viewing the first student's
  data.
- AC5 ✅ constructed a scenario where faculty1's subject shows `ABSENT`
  (0%) and faculty2's shows `PRESENT` (100%) for the same student — faculty1's
  summary reports exactly `0.0%` and only their own subject, proving the
  scoping filter is applied at the query level, not just hidden in the UI.
- AC6 ✅ a student with zero records → `percentage: null`, `by_subject: []`.

All acceptance criteria met. Proceeding to SPEC 11 (Low Attendance
Detection).

## Final Status
COMPLETE
