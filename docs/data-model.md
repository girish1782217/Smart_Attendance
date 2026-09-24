# Data Model

> This document is filled in incrementally as each spec introduces entities.
> SPEC-01 introduces no persistent entities (health check only).

## Conventions

- Every table has `id` (integer PK, autoincrement), `created_at`,
  `updated_at` (UTC datetime, server-set).
- Master-data tables additionally have `is_active` (soft delete — see
  Assumption A-10 in `sdd/00-product-spec.md`).
- All foreign keys are indexed.
- Enums are implemented as SQLAlchemy `Enum` (portable across SQLite/Postgres)
  backed by Python `enum.Enum`, not free-text strings.

## Entity index (populated per-spec)

| Entity | Introduced in | Notes |
|---|---|---|
| `users` | SPEC-02 | Identity + credentials only. Role assignment lands in SPEC-03 (`roles`/`user_roles`) as a separate concern. |
| `revoked_tokens` | SPEC-02 | Logout support for otherwise-stateless JWTs (Assumption A-2-1). Keyed by JWT `jti`; opportunistically pruned of expired rows on each write. |
| `roles` | SPEC-03 | 3 fixed rows seeded by migration: `ADMIN`, `FACULTY`, `STUDENT` (`app/core/roles.py::RoleName`). No separate `permissions` table — see the simplification note in `03-rbac-spec.md`. |
| `user_roles` | SPEC-03 | Many-to-many join, composite PK `(user_id, role_id)`, `ON DELETE CASCADE` both sides. A user may hold more than one role. |
| `departments` | SPEC-04 | Top-level org unit. `name` and `code` both unique. |
| `programs` | SPEC-04 | Belongs to a Department. `code` globally unique, `name` unique within department. |
| `academic_years` | SPEC-04 | `name` unique, `start_date < end_date` enforced. |
| `semesters` | SPEC-04 | Belongs to an AcademicYear. `name` unique within year; dates must fall within the parent year's range. |
| `classes` | SPEC-04 | Belongs to a Program (model class `AcademicClass`, table `classes` — avoids the Python `class` keyword). `name` unique within program. |
| `sections` | SPEC-04 | Belongs to a Class. `name` unique within class; optional `capacity`. |
| `subjects` | SPEC-04 | Belongs to a Department. `code` globally unique. Deliberately not nested under Section — see `04-master-data-spec.md`'s Entity Hierarchy note. |

## `users`

| Column | Type | Constraints |
|---|---|---|
| id | integer | PK, autoincrement |
| email | string(255) | unique, indexed, not null |
| full_name | string(255) | not null |
| hashed_password | string(255) | not null — bcrypt hash, never returned by any API |
| is_active | boolean | not null, default true |
| created_at | datetime | server default now |
| updated_at | datetime | server default now, updated on write |

## `revoked_tokens`

| Column | Type | Constraints |
|---|---|---|
| jti | string(64) | PK — the revoked token's JWT ID |
| revoked_at | datetime | server default now |
| expires_at | datetime | not null, indexed — the token's original expiry, used to prune stale rows |

## `roles`

| Column | Type | Constraints |
|---|---|---|
| id | integer | PK, autoincrement |
| name | string(50) | unique, indexed, not null — `ADMIN` \| `FACULTY` \| `STUDENT` |
| description | string(255) | nullable |

## `user_roles`

| Column | Type | Constraints |
|---|---|---|
| user_id | integer | PK (composite), FK → `users.id`, `ON DELETE CASCADE` |
| role_id | integer | PK (composite), FK → `roles.id`, `ON DELETE CASCADE` |

## Master data (SPEC-04)

All 7 tables include the standard `id` / `created_at` / `updated_at` /
`is_active` columns (via `TimestampMixin`/`SoftDeleteMixin`) in addition to
what's listed below.

| Table | Own columns | Constraints |
|---|---|---|
| `departments` | name, code | unique(name), unique(code) |
| `programs` | name, code, department_id | unique(code), unique(department_id, name), FK department_id → departments.id |
| `academic_years` | name, start_date, end_date | unique(name) |
| `semesters` | name, academic_year_id, start_date, end_date | unique(academic_year_id, name), FK academic_year_id → academic_years.id |
| `classes` | name, program_id | unique(program_id, name), FK program_id → programs.id |
| `sections` | name, class_id, capacity (nullable) | unique(class_id, name), FK class_id → classes.id |
| `subjects` | name, code, department_id, credits (nullable) | unique(code), FK department_id → departments.id |
| `students` | user_id, roll_number, section_id, phone (nullable) | unique(user_id), unique(roll_number), FK user_id → users.id, FK section_id → sections.id |
| `faculty` | user_id, employee_id, department_id, phone (nullable) | unique(user_id), unique(employee_id), FK user_id → users.id, FK department_id → departments.id |
| `faculty_assignments` | faculty_id, subject_id, section_id, semester_id | **partial** unique index on all 4 `WHERE is_active` (not a blanket constraint — see `06-faculty-management-spec.md` Defects), FKs to faculty/subjects/sections/semesters |
| `attendance_sessions` | faculty_id, subject_id, section_id, session_date, start_time, end_time, status | composite index (section_id, session_date) for the overlap-check query; FKs to faculty/subjects/sections; no soft-delete (status is `SCHEDULED`\|`SUBMITTED`, non-native enum for portability). Overlap prevention (no two sessions on the same section+date with intersecting time ranges) is service-layer only — not expressible as a portable DB constraint across SQLite/Postgres. |
| `attendance_records` | session_id, student_id, status, recorded_by_user_id, recorded_at | unique(session_id, student_id) — plain constraint, not partial (a record is corrected in place, never soft-deleted/recreated); status is `PRESENT`\|`ABSENT`\|`LATE`\|`EXCUSED`, non-native enum |
| `correction_requests` | attendance_record_id, original_status, requested_status, reason, requested_by_user_id, requested_at, status, reviewed_by_user_id, reviewed_at, decision_reason | **partial** unique index on `attendance_record_id` `WHERE status='PENDING'` (same pattern as SPEC-06) — at most one open request per record; a decided one never blocks a later new request |
| `audit_logs` | actor_user_id, action, entity_type, entity_id, before_value, after_value, reason, created_at | generic; introduced in SPEC-09 for the correction workflow specifically — see the Scope Note in `09-attendance-correction-spec.md` |
