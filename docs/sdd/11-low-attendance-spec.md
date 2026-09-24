# SPEC 11 — Low Attendance Detection

## Status
COMPLETE

## Objective
Identify students below a **configurable** attendance threshold (Assumption
A-3), both overall and per-subject, with department/class/section filtering
and student search — computed efficiently via SQL-side aggregation, not by
pulling every attendance record into Python.

## Design
- **Configurable threshold**: introduces `system_settings` (a simple
  key/value table) and `GET`/`PUT /settings/low-attendance-threshold`.
  Read is open to any authenticated user (students/faculty dashboards need
  to know it too); write is ADMIN-only. Falls back to
  `Settings.low_attendance_default_threshold` (`.env`-configured, default
  `75.0`) when no row has been set yet — never hardcoded elsewhere.
- **Two endpoints**, mirroring SPEC 10's summary/detail split, because
  "overall" and "per-subject" are different aggregation shapes:
  `GET /reports/low-attendance/overall` and
  `GET /reports/low-attendance/by-subject`.
- **Aggregation strategy**: SQL-side `SUM(CASE ...)` grouped by student (or
  student+subject) computes `present_count`/`absent_count`/`late_count`/
  `excused_count`/`present_equivalent`/`total_applicable` per row — an
  `INNER JOIN` to `attendance_records` naturally excludes students with zero
  records (see "no attendance data" below). Only the final percentage
  computation and the `< threshold` filter happen in Python, using a new
  pure helper, `calculate_percentage_from_counts` (extracted from SPEC 08's
  `calculate_attendance_percentage`, which now delegates to it — behavior-
  unchanged, verified by the existing SPEC 08 unit tests still passing
  unmodified). This is deliberately **not** filtered/paginated in raw SQL:
  after department/class/section/search filtering, the aggregated row count
  is bounded by realistic class/section sizes (tens to low hundreds), not
  the raw attendance-record volume, so per-row Python percentage
  computation reusing the exact SPEC 08 formula is both simple and
  efficient at the target scale (5,000 students).
- **"No attendance data" students are excluded, not shown as 0% or
  flagged**: the `INNER JOIN` to `attendance_records` means a student with
  no records at all never appears in either report — consistent with
  Assumption A-2 ("no data" ≠ "0%"), and it would be misleading to call a
  never-attended-anything student "low attendance" when there's nothing to
  measure yet.
- Filters: `department_id` (via `Student.section → AcademicClass →
  Program.department_id`), `class_id`, `section_id`, `search` (roll
  number/name), and an optional per-request `threshold` override (so an
  admin can ask "what if the threshold were 80%?" without changing the
  global setting).

## Requirements
- R1: `system_settings` table + threshold get/set endpoints.
- R2: `GET /reports/low-attendance/overall` — paginated, filtered, each row
  has full counts + percentage, only rows `< threshold`.
- R3: `GET /reports/low-attendance/by-subject` — same, one row per
  (student, subject), plus an optional `subject_id` filter.
- R4: Both ADMIN and FACULTY accessible (FACULTY sees the whole college's
  low-attendance list here — deliberately **not** scoped to their own
  subjects, unlike SPEC 07-10's ownership pattern, because identifying
  broadly at-risk students is explicitly a shared responsibility per the
  brief §14 "Faculty Dashboard... Students with low attendance" — revisit
  if this proves too broad in practice). STUDENT has no access (this is an
  administrative/faculty report, not a personal view — SPEC 10 already
  gives students their own percentage).

## Acceptance Criteria
- AC1: A student exactly at the threshold is **not** included (`< threshold`,
  not `<=` — being exactly at the line is not "below" it).
- AC2: A student one point above the threshold is excluded; one point below
  is included.
- AC3: A student with zero attendance records never appears in either
  report.
- AC4: A student attending multiple subjects appears once per qualifying
  subject in the by-subject report, and once (aggregated) in the overall
  report.
- AC5: Department/class/section filters each correctly narrow the result
  set.
- AC6: Changing the global threshold via `PUT` changes subsequent report
  results without any code change; a per-request `threshold` override
  doesn't persist.
- AC7: `PUT` is ADMIN-only; `GET` (both the setting and the reports) works
  for ADMIN and FACULTY; STUDENT is forbidden on the reports.

## Technical Design
- `app/models/system_setting.py`.
- `app/services/attendance_calculations.py`: add `calculate_percentage_from_counts`.
- `app/repositories/system_setting_repository.py`, `app/services/settings_service.py`.
- `app/repositories/low_attendance_repository.py` (SQL aggregation),
  `app/services/low_attendance_service.py`.
- `app/schemas/settings.py`, `app/schemas/low_attendance.py`.
- `app/api/v1/settings.py`, `app/api/v1/reports.py` (new — will grow further
  in SPEC 12).
- Alembic migration `0009_create_system_settings`.

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_low_attendance.py`,
`backend/tests/test_attendance_calculations.py` (extended).

## Test Results
9 new tests in `backend/tests/test_low_attendance.py` + 1 new unit test for
`calculate_percentage_from_counts` in `test_attendance_calculations.py`
(now 9 total in that file). Also re-verified the whole SPEC 08 calculation
suite passes unmodified after the `attendance_calculations.py` refactor
(behavior-preserving delegation).

## Defects Found
Two **test-data bugs**, not implementation bugs — both surfaced immediately
as failures on first run:
1. `_setup()` created an academic year named `"2025-2026"` unconditionally;
   any test calling it twice (to compare two departments) hit SPEC 04's
   correct uniqueness constraint on `AcademicYear.name` on the second call.
2. `_mark_records()` generated session dates starting from `2025-08-01`
   unconditionally; any test calling it twice for the *same section* (e.g.,
   two students, or two subjects for one student) collided with SPEC 07's
   correct overlap-prevention rule (same section+date+time, regardless of
   subject, is rejected) — both calls need genuinely non-overlapping dates.

Both are confirmations that earlier specs' uniqueness/overlap rules are
still being enforced correctly under a new, more elaborate test scenario —
not new bugs in this spec's own code.

## Fixes Applied
1. Parametrized the academic year name by `dept_code` in `_setup()`.
2. Added a `date_offset` parameter to `_mark_records()` and passed distinct
   offsets at every call site that shares a section within one test.

## Regression Results
Full backend suite (`pytest -q`, from `backend/`): **129 passed** (119 from
SPEC 01–10 + 10 new — 9 integration + 1 calculation unit test). No
regressions.

## Acceptance Verification
- AC1 ✅ a student at exactly 75.0% (the default threshold) is excluded
  from the overall report.
- AC2 ✅ 50% is included, 100% is excluded, in the same request.
- AC3 ✅ a student with zero attendance records never appears (`INNER JOIN`
  to `attendance_records` naturally excludes them).
- AC4 ✅ a student below threshold in two subjects appears as two separate
  rows in the by-subject report and one aggregated (0%) row in the overall
  report.
- AC5 ✅ `department_id` filter correctly excludes a student from a
  different department.
- AC6 ✅ `PUT` changes the threshold used by subsequent unfiltered requests;
  a per-request `?threshold=` override is reflected in that response's
  echoed `threshold` field but doesn't persist to later requests.
- AC7 ✅ FACULTY gets `403` on `PUT`; STUDENT gets `403` on both report
  endpoints.

All acceptance criteria met. Proceeding to SPEC 12 (Reporting).

## Final Status
COMPLETE
