# SPEC 07 — Attendance Session Management

## Status
COMPLETE

## Objective
Implement `AttendanceSession` — the anchor entity attendance recording
(SPEC 08) attaches to — with creation validated against real
`FacultyAssignment` rows, overlap prevention, listing, detail view, and the
student roster for a session.

## Design
- `AttendanceSession`: `faculty_id`, `subject_id`, `section_id`,
  `session_date`, `start_time`, `end_time`, `status`
  (`SCHEDULED`/`SUBMITTED` — stored as a portable non-native enum,
  `native_enum=False`, so adding a status later needs no Postgres `ALTER
  TYPE` migration), + timestamps. No `is_active`/soft-delete — a session is
  either `SCHEDULED` or `SUBMITTED`; SPEC 08 owns the transition to
  `SUBMITTED`.
- **Faculty-assignment validation**: creating a session checks an *active*
  `FacultyAssignment` exists for `(faculty_id, subject_id, section_id)` —
  any semester. **Documented simplification**: this does not cross-check
  `session_date` against the assignment's semester date range. A faculty
  member having *any* active assignment to that (subject, section)
  authorizes them; semester boundaries are enforced administratively by
  when assignments are created/deactivated (SPEC 06), not re-derived here.
  Revisit if cross-semester date drift becomes a real problem.
- **Overlap prevention**: no two sessions for the *same section* (regardless
  of subject — a section can't attend two different subjects at once) may
  have overlapping `[start_time, end_time)` on the same `session_date`.
  Enforced at the **service layer only** (not a DB constraint) — interval
  overlap isn't expressible as a portable constraint across SQLite/
  PostgreSQL without dialect-specific range types (Postgres `EXCLUDE`,
  nothing equivalent in SQLite). A composite `(section_id, session_date)`
  index keeps the overlap query cheap.
- **Ownership scoping refactor**: extracted the "ADMIN sees everything /
  FACULTY is always scoped to their own linked profile" logic that SPEC 06
  hand-rolled in `faculty_assignments.py` into `app/services/scoping.py`
  (`resolve_faculty_filter` for reads, `resolve_faculty_for_write` for
  writes — the latter requires ADMIN to supply an explicit `faculty_id`
  since there's no "own" one to default to). SPEC 06's router now uses the
  shared version — a real second consumer justifies the extraction now
  rather than speculatively.
- A FACULTY caller cannot fetch (`GET .../{id}`) or view the roster of a
  session belonging to a different faculty member, even by guessing the id.

## Requirements
- R1: Create session: validates faculty/subject/section exist, an active
  assignment connects them, and no time overlap on that section+date.
- R2: FACULTY callers always create/list sessions scoped to their own
  linked Faculty profile; ADMIN must specify `faculty_id` explicitly on
  create, or may omit it on list (meaning "all faculty").
- R3: List: filter by `section_id`/`subject_id`/`faculty_id`/date range,
  paginated.
- R4: Detail view + roster (`GET /{id}/roster` → active students currently
  in the session's section) — both ownership-checked for FACULTY callers.
- R5: STUDENT role has no access to any attendance-session endpoint (SPEC 10
  gives students a purpose-built "my attendance" view later, not raw
  session browsing).

## Acceptance Criteria
- AC1: Valid session create → `201`, `status: SCHEDULED`.
- AC2: Non-existent faculty/subject/section → distinct `404 *_NOT_FOUND`.
- AC3: Faculty with no active assignment to that (subject, section) →
  `403 FACULTY_NOT_ASSIGNED`.
- AC4: Overlapping time range on the same section+date → `409
  SESSION_TIME_OVERLAP`.
- AC5: `end_time <= start_time` → `422`.
- AC6: A FACULTY caller creating a session ignores any `faculty_id` they
  pass — it's always their own. An ADMIN caller omitting `faculty_id` → `422
  FACULTY_ID_REQUIRED`.
- AC7: A FACULTY caller cannot `GET` another faculty member's session or
  roster by id (`403`); their list only ever contains their own sessions.
- AC8: Roster returns exactly the active students in the session's section.
- AC9: STUDENT gets `403` on every endpoint in this router.

## Technical Design
- `app/models/attendance_session.py` (+ `AttendanceSessionStatus` enum).
- `app/repositories/attendance_session_repository.py`.
- `app/services/scoping.py` (new, shared) + `app/services/attendance_session_service.py`.
- `app/schemas/attendance_session.py`.
- `app/api/v1/attendance_sessions.py`.
- `app/repositories/student_repository.py`: add `list_active_by_section`.
- `app/schemas/student.py`: add `StudentResponse.from_model(...)` classmethod
  (small refactor, reused by both `students.py` and the new roster endpoint).
- Alembic migration `0006_create_attendance_sessions`.

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_attendance_sessions.py`.

## Test Results
12 new tests in `backend/tests/test_attendance_sessions.py`, covering
creation validation (FK checks, assignment check, overlap, time-order),
scoping (ADMIN vs FACULTY, cross-faculty access denial), and the roster
endpoint. All passed on first run. Verified manually: migration applies
cleanly to a real SQLite file.

## Defects Found
None — all tests passed on first implementation. (Two N+1-shaped omissions
were caught and fixed *during* implementation, before any test ran, by
re-reading the repository against the response schema's field access —
recorded here for the regression record even though no test ever went red:
`AttendanceSessionResponse.from_model` reads `session.faculty.user.full_name`,
which needs `faculty.user` eagerly joined, not just `faculty`; the initial
`_EAGER` tuple in `attendance_session_repository.py` only joined `faculty`
one level deep.)

## Fixes Applied
N/A (defect above was caught pre-test-run; no failing test to reference).

## Regression Results
Full backend suite (`pytest -v`, from `backend/`): **83 passed** (71 from
SPEC 01–06 + 12 new). No regressions. This run also re-validates the
SPEC 06 `faculty_assignments.py` refactor onto shared `scoping.py` — all
`test_faculty.py` assignment tests still pass unchanged.

## Acceptance Verification
- AC1 ✅ valid create → `201`, `status: SCHEDULED`.
- AC2 ✅ invalid `subject_id` → `404 SUBJECT_NOT_FOUND` (same pattern covers
  faculty/section, sharing the master-data `*_NOT_FOUND` convention).
- AC3 ✅ faculty with no active assignment to that (subject, section) →
  `403 FACULTY_NOT_ASSIGNED`.
- AC4 ✅ overlapping range → `409 SESSION_TIME_OVERLAP`; a back-to-back
  non-overlapping range (`10:00`–`11:00` right after `09:00`–`10:00`)
  succeeds, proving the boundary condition (`<`/`>`, not `<=`/`>=`) is
  correct.
- AC5 ✅ `end_time <= start_time` → `422`.
- AC6 ✅ FACULTY caller's spoofed `faculty_id` (a nonexistent id, `999999`)
  is silently ignored in favor of their own; ADMIN omitting `faculty_id` →
  `422 FACULTY_ID_REQUIRED`.
- AC7 ✅ a second faculty member gets `403` on both `GET .../{id}` and
  `GET .../{id}/roster` for a session they don't own, and an empty (`total:
  0`) list rather than seeing it via listing.
- AC8 ✅ roster returns exactly the active students seeded into that
  section.
- AC9 ✅ STUDENT gets `403` on list/get/create.

All acceptance criteria met. Proceeding to SPEC 08 (Attendance Recording).

## Final Status
COMPLETE
