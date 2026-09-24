# SPEC 14 — Dashboards

## Status
COMPLETE

## Objective
Three role-specific dashboard endpoints, each independently gated by
`require_role` (not a single endpoint that filters its response by role) —
the brief's own test list demands proving *backend* authorization, and a
Student hitting the Admin dashboard route should get `403`, not a
differently-shaped `200`.

## Design: reuse, don't rebuild (continued from SPEC 12)
Every metric is computed by calling an already-tested service function, not
new bespoke aggregation:
- Student dashboard's "overall" and "subject-wise" attendance = SPEC 10's
  `attendance_history_service.get_summary` verbatim.
- Student dashboard's "recent attendance" = SPEC 10's `get_history`,
  `page=1, page_size=5`.
- "Low attendance warning" = summary's overall percentage compared against
  SPEC 11's configured threshold.
- Faculty/Admin's "students with low attendance" = SPEC 11's
  `low_attendance_service`, which gains an optional `faculty_id` filter
  (additive to `low_attendance_repository`'s aggregation functions, which
  already join `attendance_sessions` and therefore already have
  `faculty_id` available — SPEC 11's existing calls are unaffected).
- Faculty's "pending correction requests" / "today's sessions" / "total
  sessions" reuse SPEC 09's `correction_repository` and SPEC 07's
  `attendance_session_repository` with existing or trivially-extended
  filters.
- A small new `dashboard_repository.py` holds only the handful of counts
  that don't already exist anywhere: active student/faculty/department/
  class counts, and a global (college-wide) attendance percentage for the
  Admin dashboard.

## Requirements
- R1: `GET /dashboard/admin` (ADMIN only): total active students/faculty/
  departments/classes, today's session counts, global attendance
  percentage, count of students below threshold (college-wide), count of
  pending correction requests (any).
- R2: `GET /dashboard/faculty` (FACULTY only, always the caller's own):
  distinct assigned sections, today's sessions, total sessions ever
  conducted, students below threshold *within this faculty's own sessions*,
  pending correction requests *for this faculty's sessions*.
- R3: `GET /dashboard/student` (STUDENT only, always the caller's own):
  overall + subject-wise attendance, 5 most recent attendance records, a
  low-attendance boolean + the threshold, and pending correction request
  count.
- R4: Every dashboard's data is scoped/filtered server-side — verified by a
  test that proves the *data itself* differs by role for the same
  underlying dataset, not merely that the wrong role gets `403`.

## Acceptance Criteria
- AC1: STUDENT gets `403` on `/dashboard/admin` and `/dashboard/faculty`;
  FACULTY gets `403` on `/dashboard/admin`; ADMIN gets `403` on neither
  (dashboards are role-exclusive, not ADMIN-can-see-everything here — an
  Admin wanting a specific faculty's view uses SPEC 12's reports instead).
- AC2: Faculty dashboard's "students with low attendance" count only
  reflects that faculty's own sessions — proven with the same
  two-faculty/two-subject scenario pattern used in SPEC 10 AC5.
- AC3: Student dashboard's "recent attendance" returns at most 5 rows, most
  recent first.
- AC4: Student dashboard's low-attendance flag flips correctly around the
  threshold (reusing SPEC 11's exact comparison).
- AC5: Admin dashboard's counts match a hand-verified small scenario
  (N students, M faculty, etc.).

## Technical Design
- `app/repositories/dashboard_repository.py` (new — the few genuinely-new
  counts).
- `app/repositories/low_attendance_repository.py`: add optional
  `faculty_id` filter to both aggregate functions.
- `app/services/low_attendance_service.py`: thread `faculty_id` through.
- `app/services/dashboard_service.py` (new — orchestrates existing service
  calls).
- `app/schemas/dashboard.py`.
- `app/api/v1/dashboard.py`.

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_dashboards.py`.

## Test Results
6 new tests in `backend/tests/test_dashboards.py`, all passed on first run.
Also re-ran SPEC 11/12's suites (`test_low_attendance.py`,
`test_reports.py`) immediately after adding the `faculty_id` filter to
`low_attendance_repository`, before writing any new test, to confirm the
additive change was truly behavior-preserving — 16/16 passed unmodified.

## Defects Found
None — all 6 new tests passed on first implementation.

## Fixes Applied
N/A.

## Regression Results
Full backend suite (`pytest -q`, from `backend/`): **149 passed** (143 from
SPEC 01–13 + 6 new). No regressions.

## Acceptance Verification
- AC1 ✅ all 9 role×dashboard combinations checked in one test: each
  dashboard returns `200` for exactly its own role and `403` for the other
  two, including ADMIN on the faculty/student dashboards.
- AC2 ✅ a two-faculty, two-subject scenario (mirroring SPEC 10's AC5
  pattern) shows faculty1's dashboard counting only their own below-
  threshold student, not faculty2's.
- AC3 ✅ 7 submitted sessions for one student yields exactly 5 rows in
  `recent_attendance`.
- AC4 ✅ a 0%-vs-100% two-student scenario flips `is_low_attendance`
  correctly for each, and both report the same `threshold` (75.0).
- AC5 ✅ a hand-built scenario (1 department, 1 class, 1 faculty, 2
  students, 0 pending corrections) matches the admin dashboard's counts
  exactly.

All acceptance criteria met. Proceeding to SPEC 15 (Gemini AI Insights).

## Final Status
COMPLETE
