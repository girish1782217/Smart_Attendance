# SPEC 00 — Product Foundation

## Status
COMPLETE

## 1. Product Scope

Build a **Smart Attendance Management System** for a college with ~5,000 students,
~200 faculty, multiple departments, classes, sections, and subjects. The system
covers the full lifecycle: academic structure setup → attendance session
creation → attendance recording → correction workflow → review/audit →
history/reporting → low-attendance detection → dashboards → AI-assisted
insights.

The system is architected to scale to the target volumes (5,000 students / 200
faculty) without structural changes: server-side pagination, indexed foreign
keys, and aggregate queries are required from the first data-bearing spec
onward, not retrofitted later.

## 2. Actors

| Actor | Description |
|---|---|
| **Admin** | Institution administrator. Manages master data, users/roles, faculty assignments, attendance thresholds; reviews/approves corrections; views all reports and audit history. |
| **Faculty** | Teaches assigned subjects to assigned sections. Records and submits attendance for their own sessions, views their students' history and low-attendance lists, participates in the correction workflow for their sessions. |
| **Student** | Views their own attendance (overall + subject-wise), history, and low-attendance warnings. Can submit correction requests but never edits attendance directly. |

A single `users` identity table backs all three; role(s) are assigned via
`user_roles`, so a user could in principle hold more than one role (e.g. a
faculty member who is also an admin), though seed data keeps them disjoint for
clarity.

## 3. Major Workflows

1. **Academic setup** — Admin creates departments, programs, academic
   years/semesters, classes, sections, subjects, faculty, students, and
   assigns faculty to (section, subject, semester) combinations.
2. **Attendance recording** — Faculty opens an assigned (section, subject)
   pairing, creates an attendance session for a date/time slot, marks each
   enrolled student PRESENT/ABSENT/LATE/EXCUSED, and submits (finalizes) it.
3. **Attendance correction** — Student or Faculty requests a change to a
   finalized record with a reason; Admin (or the owning Faculty, for their own
   session, excluding self-requests they submitted) reviews and
   approves/rejects; an approved correction updates the record and writes an
   audit entry preserving the original value.
4. **Attendance review/history** — Any authorized actor views historical
   attendance filtered by student/subject/class/section/date range, scoped by
   role (students see only themselves; faculty see their own sessions;
   admins see everything).
5. **Low-attendance detection** — System computes attendance % per
   student/subject against a configurable threshold and surfaces students
   below it, filterable by department/class/section/subject.
6. **Reporting** — Student, subject, low-attendance, and faculty-activity
   reports, filterable, paginated, exportable (CSV).
7. **Dashboards** — Role-scoped summary views (admin/faculty/student).
8. **AI insights** — Authorized users request a Gemini-generated narrative
   summary of already-computed attendance data for a student (advisory only).

## 4. Functional Requirements (summary — detailed per-spec)

FR-1. Authenticate users via JWT; support login/logout/current-user.
FR-2. Enforce role-based authorization at the API layer (never trust the
      frontend alone).
FR-3. CRUD + search/filter/sort/pagination for all master data entities.
FR-4. CRUD for students and faculty with validation and duplicate prevention.
FR-5. Attendance sessions tied to a specific (faculty, subject, section, date,
      time slot); faculty can only create sessions for their own assignments.
FR-6. Attendance recording supports PRESENT/ABSENT/LATE/EXCUSED per student
      per session, bulk marking, and a submit/finalize transition after which
      records require the correction workflow to change.
FR-7. Attendance percentage computed deterministically per the rule in §9
      of the pasted brief (formalized in §8 below) — never by the AI.
FR-8. Correction workflow preserves original values, requires a reason,
      records requester/reviewer/decision timestamps, and cannot be
      double-approved.
FR-9. All mutations to attendance records, correction decisions, and
      user/role changes write an audit log entry (actor, action, before,
      after, timestamp, reason where applicable).
FR-10. Low-attendance detection against a configurable threshold (default
      75%), overall and per-subject.
FR-11. Reports are paginated, filterable, and exportable to CSV.
FR-12. Role-scoped dashboards return only data the caller is authorized to
      see, enforced server-side.
FR-13. In-app notifications for: low attendance crossing threshold,
       correction submitted, correction approved, correction rejected.
FR-14. AI insight endpoint sends only backend-computed structured data to
       Gemini, treats the response as advisory text, never as a source of
       attendance truth; failures/timeouts degrade gracefully.

## 5. Non-Functional Requirements

NFR-1. **Security** — bcrypt password hashing, JWT with expiry, no secrets in
       source control or API responses, parameterized queries only (ORM),
       input validation via Pydantic on every endpoint.
NFR-2. **Auditability** — every attendance mutation and correction decision is
       reconstructable after the fact.
NFR-3. **Scalability** — list endpoints are paginated and indexed for the
       5,000-student / 200-faculty target; no unbounded result sets.
NFR-4. **Testability** — every spec ships with unit + integration tests (and
       E2E where a user-facing workflow is completed); Gemini calls are
       mocked in automated tests.
NFR-5. **Maintainability** — layered backend (router → service → repository →
       DB); no business logic in route handlers; reusable frontend
       components for tables/forms/filters/pagination/status badges.
NFR-6. **Usability** — responsive layout, clear empty/loading/error states,
       confirmation on destructive actions, toast feedback.
NFR-7. **Portability** — DATABASE_URL-driven persistence; SQLite for
       dev/test, Postgres-compatible schema/queries for production (see
       Assumption A-1).

## 5a. Spec Numbering Resolution

The brief's own §2 file list and §23 spec breakdown disagree (§2 omits a
dedicated RBAC file and shifts subsequent numbers by one, and folds
class/section/subject into a file not present in §23's numbered list). §23's
breakdown is authoritative for this project (00 Product, 01 Foundation, 02
Auth, 03 RBAC, 04 Master Data, ... 18 Acceptance) — it is the more detailed,
explicitly-numbered source, matches the DB design in §18 (which groups
department/program/academic-year/semester/class/section/subject together as
one "master data" concern), and is what SPEC 00–03 have already been built
against. `docs/sdd/` filenames follow §23's numbers.

## 6. Assumptions (materially resolved ambiguities)

Each assumption below was made because the underlying decision would not
change the architecture materially, or a reasonable industry-standard default
exists. All are revisitable.

- **A-1 (Database engine)** — No PostgreSQL server was available in the dev
  environment. Per explicit user decision: SQLite is used for dev/test via
  `DATABASE_URL`; the schema and ORM usage avoid Postgres/SQLite-incompatible
  constructs (no native arrays, no JSONB-only operators) so the same code
  runs against PostgreSQL in production by changing `DATABASE_URL` alone.
- **A-2 (Attendance percentage formula)** — `EXCUSED` sessions are removed
  from *both* numerator and denominator (an excused absence never penalizes a
  student). `LATE` counts as a full present-equivalent (the student did
  attend). Formula:
  `% = (PRESENT + LATE) / (PRESENT + ABSENT + LATE) × 100`, with 0 sessions
  applicable reported as "no data" rather than 0% or 100%. Documented in
  detail in `07-attendance-recording-spec.md` and `11-low-attendance-spec.md`.
- **A-3 (Low-attendance threshold)** — Stored as a single system-wide
  configurable setting (`system_settings` table), default `75.0`, editable
  only by Admin. Per-department/class overrides are out of scope for v1
  (documented below).
- **A-4 (Correction reviewer)** — Admin can review any correction. Faculty can
  review corrections for sessions they own, but not ones they themselves
  requested (segregation of duties) — those escalate to Admin only.
- **A-5 (Session granularity)** — One attendance session = one (section,
  subject, faculty, date, start_time, end_time) combination. A section/subject
  pair cannot have two sessions with overlapping time ranges on the same date
  (enforced at the service layer).
- **A-6 (Student enrollment)** — A student belongs to exactly one (class,
  section) at a time for a given academic year/semester; the roster for a
  session is derived from that assignment. Multi-elective/mixed-section
  subjects are out of scope for v1.
- **A-7 (Notifications)** — In-app only (no email/SMS), per explicit
  instruction in the brief.
- **A-8 (AI provider)** — Google Gemini via `GEMINI_API_KEY`, called
  server-side only, mocked in all automated tests; missing/invalid key
  degrades the feature (503-style advisory error) rather than breaking the
  app.
- **A-9 (Auth token transport)** — JWT bearer token (not server-side session
  store), access-token only for v1 (no refresh-token rotation), short expiry
  (60 min) — acceptable for an assessment-scope project; documented as a
  known limitation.
- **A-10 (Soft delete)** — Master data (department/program/class/section/
  subject/faculty/student) uses soft delete (`is_active` flag) so historical
  attendance keeps valid references; hard delete is not exposed via the API.

## 7. Business Rules (canonical list — see per-spec detail)

- BR-1: A student cannot have two attendance records for the same session.
- BR-2: A faculty member may only create/record sessions for (section,
  subject) pairs they are assigned to for the active semester.
- BR-3: Once a session is submitted/finalized, individual records can only be
  changed through an approved correction request.
- BR-4: A correction request must reference an existing attendance record and
  cannot be approved twice (idempotent state machine: `PENDING → APPROVED |
  REJECTED`, terminal).
- BR-5: Students can never write attendance records directly (create,
  update, or correction-approve).
- BR-6: Attendance percentage and low-attendance status are always computed
  server-side; the UI and AI never compute or invent these figures.
- BR-7: All list endpoints exposing >1 page of data implement pagination;
  default page size 25, max 100.

## 8. Out of Scope (v1)

- Biometric/QR/geolocation-based attendance capture (business problem only
  requires recording, not capture-hardware integration).
- Email/SMS notification delivery.
- Multi-institution / multi-tenant support.
- Refresh-token rotation, SSO/OAuth.
- Per-department/per-class threshold overrides (single global threshold only).
- Mobile native apps (responsive web only).
- PDF export (CSV export only; PDF documented as a future improvement).

## 9. Acceptance Criteria (product-level)

- AC-1: A user with role Admin can complete Workflow 1 (create full academic
  structure) end-to-end via the API and UI.
- AC-2: A user with role Faculty can complete Workflow 2 (session → mark →
  submit) end-to-end, and cannot perform Admin-only master-data mutations.
- AC-3: A user with role Student can view Workflow 3 (own attendance/history)
  and cannot write any attendance record.
- AC-4: Workflow 4 (correction request → review → approve → audit) is
  provable via the audit log, including the original value being preserved.
- AC-5: Workflow 5 (low-attendance report, filter, export) returns
  server-computed, correctly-filtered data.
- AC-6: Workflow 6 (AI insight) returns a Gemini-generated narrative built
  only from backend-computed numbers, and degrades gracefully when Gemini is
  unavailable.
- AC-7: Every specification below is marked COMPLETE only when its own tests
  pass and the full regression suite still passes.

## 10. Requirements Traceability Seed

See `/docs/traceability-matrix.md` (created alongside this spec, updated after
every subsequent spec).
