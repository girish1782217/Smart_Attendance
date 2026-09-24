# SPEC 13 — Notifications

## Status
COMPLETE

## Objective
In-app notifications (Assumption A-7 — no email/SMS) for the four events the
brief names: correction requested, correction approved, correction
rejected, and low attendance.

## Design
- `Notification`: `user_id` (recipient), `type`, `title`, `message`,
  `related_entity_type`/`related_entity_id` (generic pointer, e.g. back to
  the correction request), `is_read`, `created_at`, `read_at`.
- **Correction requested** → notifies the session's owning faculty member
  (the primary reviewer) — *unless* they are the requester themselves (a
  faculty member correcting their own session's record has nothing to be
  notified of; Admin discovers pending items via the reports/dashboard
  instead of a blanket notify-all-admins fan-out, which would be noisy for
  no clear benefit at this scale).
- **Correction approved/rejected** → notifies the original requester
  (student or faculty).
- **Low attendance** → triggered at the one natural point attendance
  actually changes in a way that could newly cross the threshold:
  **session submission** (SPEC 08). After a session is finalized, every
  student in its roster has their overall percentage recomputed (reusing
  SPEC 10's `attendance_history_service.get_summary`); anyone now below the
  configured threshold (SPEC 11) gets notified — **unless they already have
  an unread low-attendance notification** (duplicate prevention: don't pile
  up repeat alerts for an ongoing condition the student hasn't acknowledged
  yet; once they mark it read, a later re-drop below threshold notifies
  again).
- Notifications are strictly per-user: every endpoint operates on the
  caller's own notifications only (`get_current_user`, not `require_role`
  with a list — any authenticated role may have notifications).

## Requirements
- R1: `Notification` model + the four creation triggers wired into existing
  services (`correction_service`, `attendance_record_service`) — no new
  endpoints act as the trigger; existing actions (request/approve/reject/
  submit) grow a notification side-effect.
- R2: `GET /notifications` — paginated, filterable by `is_read`, own-user
  only.
- R3: `GET /notifications/unread-count` — small utility for a UI badge.
- R4: `POST /notifications/{id}/read` — mark one's own notification read;
  `404` (not `403`) for someone else's id, to avoid confirming it exists.
- R5: `POST /notifications/mark-all-read` — convenience bulk action.
- R6: Duplicate prevention for low-attendance notifications as described
  above.

## Acceptance Criteria
- AC1: Requesting a correction notifies the owning faculty (when they
  didn't request it themselves); no notification is created when they did.
- AC2: Approving/rejecting notifies the original requester with the correct
  type.
- AC3: A user's `GET /notifications` never includes another user's
  notifications.
- AC4: Marking a notification read updates `is_read`/`read_at`; marking
  someone else's by id → `404`.
- AC5: Submitting a session that leaves a student below threshold creates
  exactly one `LOW_ATTENDANCE_WARNING`; submitting a second session that
  keeps them below threshold does **not** create a second one while the
  first remains unread; marking it read and then dropping further creates a
  new one.
- AC6: `unread-count` reflects only unread notifications for the caller.

## Technical Design
- `app/models/notification.py`.
- `app/repositories/notification_repository.py`.
- `app/services/notification_service.py` (creation helpers +
  read/list/mark-read logic).
- Wiring: `correction_service.py` (request/approve/reject call the notify
  helpers), `attendance_record_service.py` (`submit_session` calls
  `check_and_notify_low_attendance`).
- `app/schemas/notification.py`.
- `app/api/v1/notifications.py`.
- Alembic migration `0010_create_notifications`.

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_notifications.py`.

## Test Results
7 new tests in `backend/tests/test_notifications.py`, covering all four
notification triggers, per-user isolation, mark-read ownership, and the
low-attendance dedup behavior across three successive submissions.

## Defects Found
Two **test-data bugs**, not implementation bugs:
1. Several tests used a 2-student section but only marked *one* student
   per session before submitting — SPEC 08's "complete roster" rule
   correctly rejected the submit with `INCOMPLETE_ROSTER`, since the other
   student was left unmarked. Fixed by extending the `_mark_and_submit`
   test helper to accept `other_student_ids` and mark them `PRESENT` so the
   roster is always complete, regardless of how many students exist in the
   section for unrelated reasons.
2. `test_mark_read_updates_state_and_rejects_other_users_notification`
   marked its test student `ABSENT` (a habit carried over from other test
   files) without realizing this spec's own submit-time side effect would
   *also* fire a `LOW_ATTENDANCE_WARNING` for that student — so after
   marking the one notification the test cared about as read, one
   notification (the low-attendance warning) legitimately remained unread,
   and the test's `unread_count == 0` assertion was simply wrong about the
   scenario it had built. Fixed by marking the student `PRESENT` instead
   (this test is about mark-read/ownership, not low-attendance), removing
   the confound entirely rather than adjusting the assertion around it.

## Fixes Applied
See above — both were test-setup corrections, verified by re-running to
green immediately after.

## Regression Results
Full backend suite (`pytest -q`, from `backend/`): **143 passed** (136 from
SPEC 01–12 + 7 new). No regressions — in particular, SPEC 08's
`test_attendance_recording.py` and SPEC 09's `test_corrections.py` still
pass unmodified despite both `submit_session` and the correction
request/approve/reject functions gaining new notification side effects.

## Acceptance Verification
- AC1 ✅ owning faculty gets notified on request; self-requesting faculty
  member creates zero notifications for themselves.
- AC2 ✅ approve/reject each notify the original requester with the correct
  `type`.
- AC3 ✅ a second student's notification list never includes another
  student's notification, even after that other student's correction is
  decided.
- AC4 ✅ marking one's own notification read updates `is_read`/`read_at`;
  another user's id → `404`.
- AC5 ✅ a 3-submission sequence (below-threshold, still-below-threshold,
  read-then-below-threshold-again) produces exactly 1, then still 1, then 2
  total notifications — proving both the creation and the dedup logic.
- AC6 ✅ `unread-count` reflects exactly the caller's own unread rows.

All acceptance criteria met. Proceeding to SPEC 14 (Dashboards).

## Final Status
COMPLETE
