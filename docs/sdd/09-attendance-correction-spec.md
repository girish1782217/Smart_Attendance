# SPEC 09 — Attendance Correction

## Status
COMPLETE

## Objective
Implement the controlled correction workflow (BR-3/BR-4/§11 of the brief):
`Requested → Reviewed → Approved|Rejected`, with the original value always
preserved, and introduce the first genuine `audit_logs` entries (scoped to
this workflow — see Scope Note).

## Design
- `CorrectionRequest`: `attendance_record_id`, `original_status` (snapshot
  at request time — never re-derived), `requested_status`, `reason`,
  `requested_by_user_id`, `requested_at`, `status`
  (`PENDING`/`APPROVED`/`REJECTED`), `reviewed_by_user_id`, `reviewed_at`,
  `decision_reason`. Partial unique index on `attendance_record_id` `WHERE
  status = 'PENDING'` (same pattern as SPEC 06's `FacultyAssignment` — at
  most one open request per record at a time; approving/rejecting frees it
  up for a new request).
- `AuditLog`: generic (`actor_user_id`, `action`, `entity_type`,
  `entity_id`, `before_value`, `after_value`, `reason`, `created_at`) —
  written on request/approve/reject.
- **Corrections only apply to finalized records**: a request can only be
  created for a record whose session is already `SUBMITTED`
  (`409 SESSION_NOT_SUBMITTED` otherwise) — while a session is still
  `SCHEDULED`, SPEC 08's `PUT /records` already handles direct fixes; the
  heavier request/approve workflow only matters once direct editing is
  closed off.
- **Who can request**: STUDENT (their own record only), FACULTY (only for
  sessions they own), ADMIN (any). A no-op request (`requested_status ==`
  current status) is rejected (`422 NO_CHANGE_REQUESTED`).
- **Who can review** (Assumption A-4): ADMIN (any pending request); FACULTY
  only for sessions they own, and **never** a request they submitted
  themselves (`403 SELF_REVIEW_NOT_ALLOWED` — must escalate to Admin).
  STUDENT can never review.
- **Approval** applies `requested_status` to the `AttendanceRecord`
  (updating `recorded_by_user_id`/`recorded_at` to reflect the reviewer),
  marks the request `APPROVED`, and writes an audit entry. **Rejection**
  leaves the record untouched, marks the request `REJECTED`, and still
  writes an audit entry (for a complete record of what was decided and
  why). Approving/rejecting an already-decided request →
  `409 CORRECTION_ALREADY_DECIDED` (BR-4's "cannot be approved twice").
- **Listing is role-scoped** (reuses/extends `app/services/scoping.py`):
  ADMIN sees everything; FACULTY sees requests on sessions they own;
  STUDENT sees requests on their own records — regardless of who actually
  submitted the request (a faculty-submitted request about a student's
  attendance still shows up in that student's own list).

## Scope Note (audit logging)
`audit_logs` is introduced here because SPEC 09 is the first spec with an
explicit, testable "audit record created" acceptance criterion. It is
**not** retroactively wired into SPEC 02–08's mutations in this pass — doing
that for every prior endpoint is a larger, separate effort better scoped
explicitly (SPEC 16 security hardening can extend coverage using this same
`AuditLog` model/`audit_service.log(...)` helper if broader coverage becomes
a stated requirement).

## Requirements
- R1: `POST /attendance-records/{id}/corrections` — create a request,
  validated as above.
- R2: `POST /corrections/{id}/approve` and `.../reject` — the review
  actions, with the segregation-of-duties and idempotency rules above.
- R3: `GET /corrections` — paginated, role-scoped, filterable by `status`
  and `attendance_record_id`.
- R4: `GET /corrections/{id}` — detail, ownership-checked the same way as
  the list.
- R5: Every approve/reject writes an `AuditLog` row with the before/after
  status and the decision reason.

## Acceptance Criteria
- AC1: A student requests a correction on their own record → `201`,
  `status: PENDING`, `original_status` captured correctly.
- AC2: A student cannot request a correction on another student's record
  (`403`); a faculty member cannot request one for a session they don't own
  (`403`).
- AC3: Requesting a correction for a record in a non-`SUBMITTED` session →
  `409 SESSION_NOT_SUBMITTED`.
- AC4: A second `PENDING` request on the same record while one is already
  open → `409 CORRECTION_ALREADY_PENDING`.
- AC5: Admin approves → record's `status` updates to `requested_status`;
  `original_status` on the correction row is unchanged (history preserved).
- AC6: Faculty cannot approve/reject their own submitted request, even for
  a session they own (`403 SELF_REVIEW_NOT_ALLOWED`); Admin can always
  decide it.
- AC7: Approving or rejecting an already-decided request → `409
  CORRECTION_ALREADY_DECIDED`.
- AC8: Rejecting leaves the underlying `AttendanceRecord.status` unchanged.
- AC9: Every approve/reject produces exactly one new `AuditLog` row with
  correct `before_value`/`after_value`.
- AC10: A student's `GET /corrections` list contains only requests about
  their own records, regardless of requester.

## Technical Design
- `app/models/correction_request.py`, `app/models/audit_log.py`.
- `app/repositories/correction_repository.py`, `app/repositories/audit_log_repository.py`
  (thin), plus `get_by_id` added to `attendance_record_repository.py`.
- `app/services/audit_service.py`, `app/services/correction_service.py`.
- `app/services/scoping.py`: add `resolve_own_student_id`.
- `app/schemas/correction.py`.
- `app/api/v1/corrections.py` (new top-level router) + a nested
  `POST /attendance-records/{id}/corrections` route (added to a new
  `app/api/v1/attendance_records.py` router, since this is the first
  endpoint addressing an `AttendanceRecord` directly by its own id rather
  than session-scoped).
- Alembic migration `0008_create_corrections_and_audit_logs`.

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_corrections.py`.

## Test Results
10 new tests in `backend/tests/test_corrections.py`, including a dedicated
test that queries the `audit_logs` table directly (not just the API
response) to verify exactly one row is written per approve/reject with the
correct `before_value`/`after_value`/`reason`. All passed on first run.
Verified manually: migration applies cleanly to a real SQLite file, and the
partial unique index's DDL was inspected directly (`CREATE UNIQUE INDEX
uq_correction_pending_per_record ON correction_requests
(attendance_record_id) WHERE status = 'PENDING'`) — correct on the first
attempt this time, applying the lesson from SPEC 06's defect.

## Defects Found
None — all 10 new tests passed on first implementation.

## Fixes Applied
N/A.

## Regression Results
Full backend suite (`pytest -v`, from `backend/`): **111 passed** (101 from
SPEC 01–08 + 10 new). No regressions.

## Acceptance Verification
- AC1 ✅ student requests correction on their own record → `201`, `PENDING`,
  `original_status` correctly snapshotted as `ABSENT`.
- AC2 ✅ student on another student's record → `403`.
- AC3 ✅ request against a record in a `SCHEDULED` (not yet submitted)
  session → `409 SESSION_NOT_SUBMITTED`.
- AC4 ✅ a second request while one is `PENDING` → `409
  CORRECTION_ALREADY_PENDING`.
- AC5 ✅ admin approval updates the record's `status`; the correction row's
  own `original_status` remains `ABSENT` afterward (history preserved).
- AC6 ✅ the requesting faculty member gets `403 SELF_REVIEW_NOT_ALLOWED`;
  admin can still decide the same request immediately after.
- AC7 ✅ approving a request a second time → `409 CORRECTION_ALREADY_DECIDED`.
- AC8 ✅ after rejection, the underlying record's status is confirmed
  unchanged via a follow-up `GET .../records` call.
- AC9 ✅ direct DB query confirms exactly one `AuditLog` row per approve and
  per reject, with correct `entity_id`/`before_value`/`after_value`/`reason`.
- AC10 ✅ a student's `GET /corrections` list contains only the one request
  about their own record, not their classmate's.

All acceptance criteria met. Proceeding to SPEC 10 (Attendance History).

## Final Status
COMPLETE
