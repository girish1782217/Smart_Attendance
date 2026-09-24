# SPEC 12 — Reporting

## Status
COMPLETE

## Objective
Add the two report types not yet covered by SPEC 10 (student-centric, single
student) or SPEC 11 (low-attendance-only): a cross-student **Student
Attendance Report** and a cross-student **Subject Attendance Report** —
both showing *everyone* matching the filters, not just those below
threshold — plus a lightweight **Faculty Activity Report**, and **CSV
export** for the reports the brief explicitly calls out.

## Design: reuse, don't rebuild
SPEC 11's `low_attendance_repository.aggregate_overall`/`aggregate_by_subject`
already do exactly the SQL-side aggregation these reports need (per-student
or per-student-per-subject counts + percentage) — the only difference is
**no `< threshold` filter**. Rather than duplicating the aggregation
queries:
- Both repository functions gain optional `student_id`, `from_date`,
  `to_date` filters (generalizing them beyond low-attendance-specific use;
  all new parameters default to `None`, so SPEC 11's existing calls and
  tests are unaffected).
- A new `report_service.py` calls the same repository functions but skips
  the threshold cutoff, sorting by roll number instead of ascending
  percentage.
- Response rows reuse `LowAttendanceOverallRow`/`LowAttendanceBySubjectRow`
  (aliased as `StudentAttendanceRow`/`SubjectAttendanceRow` in
  `app/schemas/reports.py`) — the shape is genuinely identical.

## Faculty Activity Report (scope: minimal, per brief's "where useful")
`GET /reports/faculty-activity` — total/scheduled/submitted session counts
for a faculty member over an optional date range. Reuses SPEC 07's
`attendance_session_repository` counts rather than new aggregation.
FACULTY is auto-scoped to their own activity (same `scoping` pattern as
everywhere else); ADMIN can query any `faculty_id`.

## CSV Export
Added for the three reports the brief names explicitly (Student, Subject,
Low Attendance) — **not** for Faculty Activity, which the brief marks as
optional ("where useful") and is a single small summary object, not a
tabular list that benefits from export. Export endpoints
(`.../export`) return the **full filtered, unpaginated** result set as
`text/csv` (that's the point of exporting — pagination is a UI/API
convenience, not something a spreadsheet download should be limited by).

## Requirements
- R1: `GET /reports/student-attendance` — all students matching
  department/class/section/subject/date-range/search filters, with full
  counts + percentage per row (no threshold cutoff).
- R2: `GET /reports/subject-attendance` — same shape, one row per
  (student, subject), optional `subject_id` filter.
- R3: `GET /reports/faculty-activity` — session counts for a faculty member.
- R4: `.../export` variants for R1, R2, and both SPEC 11 low-attendance
  endpoints, returning complete (unpaginated) CSV.
- R5: Authorization: ADMIN + FACULTY (same as SPEC 11 — these are
  administrative/teaching reports, not personal student views).

## Acceptance Criteria
- AC1: Student Attendance Report includes students both above and below
  threshold (proves it's not silently reusing SPEC 11's cutoff).
- AC2: `from_date`/`to_date` correctly narrow the aggregation window.
- AC3: Subject Attendance Report with no `subject_id` shows all subjects;
  with `subject_id` shows only that one.
- AC4: Faculty Activity Report's counts match a hand-verified scenario
  (N scheduled, M submitted).
- AC5: CSV export returns `Content-Type: text/csv`, a header row, and every
  matching row — including ones that wouldn't fit on the first page at the
  default page size (proving export isn't silently truncated to one page).
- AC6: STUDENT role is forbidden on every endpoint in this spec.

## Technical Design
- `app/repositories/low_attendance_repository.py`: generalize filters
  (additive, backward-compatible).
- `app/services/report_service.py` (new).
- `app/services/csv_export.py` (new, tiny shared CSV builder).
- `app/schemas/reports.py` (new).
- `app/api/v1/reports.py`: add the new endpoints (extends SPEC 11's file).

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_reports.py`.

## Test Results
7 new tests in `backend/tests/test_reports.py`, all passed on first run.
Also did two small in-flight cleanups caught during implementation review
(before any test ran): removed a genuinely duplicate repository call in
`get_faculty_activity_report` (copy-paste artifact — the same query was
issued twice under different local names), and replaced a
`page_size=1_000_000` "fetch everything" hack with a proper
`attendance_session_repository.list_all(...)` function.

## Defects Found
None — all 7 new tests passed on first implementation.

## Fixes Applied
N/A (the two cleanups above were code-quality fixes caught during
self-review, not defects surfaced by a failing test).

## Regression Results
Full backend suite (`pytest -q`, from `backend/`): **136 passed** (129 from
SPEC 01–11 + 7 new). No regressions — in particular, SPEC 11's
`test_low_attendance.py` (9 tests) still passes unmodified after
generalizing `low_attendance_repository`'s filters and refactoring
`low_attendance_service` into full/paginated variants.

## Acceptance Verification
- AC1 ✅ a scenario with one low (0%) and one high (100%) student both
  appear in `/reports/student-attendance` — proves it's not reusing SPEC
  11's threshold cutoff.
- AC2 ✅ `from_date`/`to_date` correctly narrows a 2-session, 2-month
  scenario down to the 1 session in range.
- AC3 ✅ omitting `subject_id` returns rows for 2 subjects; supplying it
  returns only 1.
- AC4 ✅ a hand-built 1-submitted + 1-scheduled scenario reports
  `total_sessions: 2, submitted_sessions: 1, scheduled_sessions: 1` exactly.
- AC5 ✅ CSV export returns `text/csv` and all 3 seeded rows (verified by
  parsing the response with Python's own `csv.DictReader`, not just
  checking a row count).
- AC6 ✅ STUDENT gets `403` on every endpoint added in this spec, including
  the export variant.

All acceptance criteria met. Proceeding to SPEC 13 (Notifications).

## Final Status
COMPLETE
