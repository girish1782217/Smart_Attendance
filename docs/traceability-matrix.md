# Requirements Traceability Matrix

Updated after every specification is marked COMPLETE. `Test Result` reflects
the last full regression run.

| Req ID | Description | Spec | Implementation | Tests | Result |
|---|---|---|---|---|---|
| REQ-FOUND-001 | Backend boots, `/health` works | SPEC-01 | `backend/app/main.py`, `backend/app/api/health.py` | `backend/tests/test_health.py`, `backend/tests/test_error_handling.py` | PASS (4/4) |
| REQ-FOUND-002 | Frontend boots, reaches backend health check | SPEC-01 | `frontend/src/App.tsx`, `frontend/src/components/HealthStatus.tsx` | `frontend/src/components/__tests__/HealthStatus.test.tsx` | PASS (2/2) |
| REQ-AUTH-001 | Login issues JWT | SPEC-02 | `app/services/auth_service.py`, `POST /api/v1/auth/login` | `test_auth.py` | PASS (14/14) |
| REQ-AUTH-002 | Protected routes reject missing/invalid/expired/revoked tokens | SPEC-02 | `app/api/deps.py::get_current_user` | `test_auth.py` | PASS (14/14) |
| REQ-RBAC-001 | Role-gated endpoints enforce permissions server-side | SPEC-03 | `app/api/deps.py::require_role`, `app/api/v1/users.py` | `test_rbac.py` | PASS (23/23) |
| REQ-MASTER-001 | Master data CRUD + validation + pagination | SPEC-04 | `app/api/v1/master_data/*` (7 routers), `app/repositories/crud_base.py` | `test_master_data.py` | PASS (48/48) |
| REQ-STUDENT-001 | Student CRUD, dedup, search/filter/pagination | SPEC-05 | `StudentService` | `test_students.py` | PENDING |
| REQ-FACULTY-001 | Faculty CRUD + assignments | SPEC-06 | `FacultyService`, `FacultyAssignment` | `test_faculty.py` | PENDING |
| REQ-SESSION-001 | Attendance session creation & validation | SPEC-07 | `AttendanceSessionService` | `test_attendance_sessions.py` | PENDING |
| REQ-ATT-001 | Attendance recording (all statuses, bulk, submit) | SPEC-08 | `AttendanceService` | `test_attendance_recording.py` | PENDING |
| REQ-ATT-002 | Attendance % computed per documented formula | SPEC-08/11 | `attendance_calculations.py` | `test_attendance_calculations.py` | PENDING |
| REQ-CORR-001 | Correction request/review/approve/reject + audit | SPEC-09 | `CorrectionService` | `test_corrections.py` | PENDING |
| REQ-HIST-001 | Attendance history filtering | SPEC-10 | `HistoryService` | `test_history.py` | PENDING |
| REQ-LOW-001 | Low-attendance detection vs configurable threshold | SPEC-11 | `LowAttendanceService` | `test_low_attendance.py` | PENDING |
| REQ-REPORT-001 | Student/subject/low-attendance/faculty reports + export | SPEC-12 | `ReportService` | `test_reports.py` | PENDING |
| REQ-NOTIF-001 | In-app notifications for key events | SPEC-13 | `NotificationService` | `test_notifications.py` | PENDING |
| REQ-DASH-001 | Role-scoped dashboards, server-enforced | SPEC-14 | `DashboardService` | `test_dashboards.py` | PENDING |
| REQ-AI-001 | Gemini insight, backend-only, mocked in tests, graceful failure | SPEC-15 | `GeminiInsightService` | `test_ai_insights.py` | PENDING |
| REQ-SEC-001 | Security hardening pass | SPEC-16 | various | `test_security.py` | PENDING |
| REQ-UX-001 | UI/UX polish pass | SPEC-17 | frontend | manual + `frontend` tests | PENDING |
| REQ-E2E-001 | Full workflows 1–6 pass end-to-end | SPEC-18 | Playwright | `e2e/*.spec.ts` | PENDING |

Legend: PENDING (not yet implemented) → RUNNING (implemented, tests executing)
→ PASS / FAIL.
