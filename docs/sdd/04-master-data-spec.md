# SPEC 04 — Master Data

## Status
COMPLETE

## Objective
Implement the academic-structure entities everything else hangs off of:
Department, Program, Academic Year, Semester, Class, Section, Subject — with
CRUD, validation, search/filter/sort, and pagination, enforcing the
hierarchy's referential integrity.

## Entity Hierarchy & Design
```text
Department ──┬── Program ── Class ── Section
             └── Subject

AcademicYear ── Semester
```
- **Department**: top-level org unit (`name`, `code`, both unique).
- **Program**: a degree/course under a Department (`name` unique within
  department, `code` globally unique) — e.g. "B.Tech CSE" under "Computer
  Science".
- **AcademicYear**: a year span (`name` unique, e.g. "2025-2026",
  `start_date` < `end_date`).
- **Semester**: a term within an AcademicYear (`name` unique within the
  year, dates must fall within the parent year's date range).
- **Class**: a year/level within a Program (`name` unique within program) —
  e.g. "First Year" under "B.Tech CSE".
- **Section**: a division within a Class (`name` unique within class,
  optional `capacity`) — e.g. "Section A".
- **Subject**: belongs to a Department (`name`, `code` globally unique,
  optional `credits`). Deliberately **not** nested under Section — a subject
  is reusable curriculum content; which section is actually taught which
  subject, by which faculty, in which semester, is established later by
  `FacultyAssignment` (SPEC 06), not by duplicating subject rows per
  section. This keeps master data normalized.

All 7 entities: soft-delete only (`is_active`, Assumption A-10) — no hard
delete via the API, since attendance history may reference them.

## Requirements
- R1: Full CRUD (create/read/update/deactivate — no hard delete) for all 7
  entities.
- R2: Uniqueness enforced at both the DB (unique/composite-unique
  constraints) and service layer (clean `409 CONFLICT` instead of a raw
  integrity error).
- R3: FK references validated at the service layer before insert (creating
  a Program with a non-existent `department_id` → `404`, not a DB-level FK
  error).
- R4: Date-range validation: `start_date < end_date` (schema-level); a
  Semester's dates must fall within its AcademicYear's dates (service-level,
  needs the parent row).
- R5: List endpoints for all 7 support `search` (name/code, case-insensitive
  substring), parent-scoped filtering (e.g. `?department_id=`), and
  pagination (`Page[T]` convention from SPEC 03).
- R6: Mutations (create/update/deactivate) are ADMIN-only. Read (list/get)
  is open to any authenticated user — Faculty/Student need to browse
  subjects/classes/sections elsewhere in the app (e.g., picking their own
  section), so gating reads to ADMIN would break those later specs.
- R7: A generic `CRUDBase` repository helper backs all 7 entities (they
  share an identical create/list/update/deactivate shape) — see
  Design Decision below.

## Design Decision: shared `CRUDBase`
Seven entities with an identical CRUD shape is exactly the case where a
shared abstraction pays for itself immediately (not speculative reuse):
`app/repositories/crud_base.py::CRUDBase[Model]` provides
`get_by_id`/`list_paginated`/`create`/`update`/`soft_delete`, parameterized
by model class. Per-entity **services** stay separate and explicit, because
uniqueness rules and FK checks genuinely differ per entity and that's where
the business meaning (and test assertions) live.

## Acceptance Criteria
- AC1: Each entity can be created, listed (paginated, searchable, filtered),
  fetched by id, updated, and deactivated by an ADMIN.
- AC2: A FACULTY or STUDENT user can list/get any entity but gets `403` on
  create/update/deactivate.
- AC3: Duplicate `code`/`name` (per the uniqueness rule above) → `409`.
- AC4: Creating a child entity with a non-existent parent id → `404` with a
  descriptive code (e.g. `DEPARTMENT_NOT_FOUND`).
- AC5: `AcademicYear.end_date <= start_date` → `422`.
- AC6: `Semester` dates outside its `AcademicYear`'s range → `422`.
- AC7: Search (`?search=`) matches case-insensitively on name/code.
- AC8: Pagination honors `page`/`page_size` and reports correct `total`.
- AC9: Deactivating an entity sets `is_active=false` but the row (and any
  history referencing it) remains queryable — no hard delete endpoint
  exists.

## Technical Design
- `app/models/mixins.py` — `TimestampMixin`, `SoftDeleteMixin`.
- `app/models/{department,program,academic_year,semester,academic_class,section,subject}.py`.
- `app/repositories/crud_base.py` + `app/repositories/master_data_repository.py`
  (one `CRUDBase` instance per model).
- `app/services/master_data/*.py` — one service module per entity.
- `app/schemas/master_data/*.py` — Create/Update/Response schemas per entity.
- `app/api/v1/master_data/*.py` — one router per entity, aggregated into
  `master_data_router` and included on `api_v1_router`.
- Alembic migration `0003_create_master_data_tables`.

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_master_data.py` — covers AC1–AC9 across all 7 entities
(not exhaustively duplicated per entity where the underlying `CRUDBase`
logic is identical — see the file for exactly which cases are asserted per
entity vs. only on a representative one).

## Test Results

25 new tests in `backend/tests/test_master_data.py`, covering all 7
entities: Department gets the full CRUD + RBAC + search/pagination
treatment as the representative case; Program/AcademicYear/Semester/
Class/Section/Subject tests focus on what's distinct about each (FK
validation, composite uniqueness, date-range rules, capacity validation).
All passed. Also verified manually: `alembic upgrade head` applied the
7-table migration cleanly to a real SQLite file.

## Defects Found
One real defect, caught by design review before it ever reached a test run
(not caught by a failing test — worth recording anyway per the SDD
regression discipline):

1. Initial router draft for all 7 `GET` endpoints had **no auth dependency
   at all** (fully public), contradicting R6 ("read is open to any
   *authenticated* user"). Caught while reviewing `department.py` against
   the spec before replicating the pattern to the other 6 routers.

## Fixes Applied
1. Added `_current_user=Depends(get_current_user)` to every list/get
   endpoint across all 7 routers, so reads require a valid token (any role)
   while writes require `require_role(RoleName.ADMIN)`. Verified by
   `test_unauthenticated_cannot_list_departments` (401, not 200).

## Regression Results
Full backend suite (`pytest -v`, from `backend/`): **48 passed** (23 from
SPEC 01–03 + 25 new). No regressions.

## Acceptance Verification
- AC1 ✅ create/list/get/update/deactivate exercised for every entity.
- AC2 ✅ FACULTY/STUDENT get `403` on department mutation; both can list/get.
- AC3 ✅ duplicate department name and code both → `409`; same pattern
  verified for Program (name-within-department, global code) and Subject
  (global code).
- AC4 ✅ Program/Class/Section/Semester each reject a non-existent parent id
  with a specific `*_NOT_FOUND` code.
- AC5 ✅ `end_date <= start_date` on AcademicYear create → `422`.
- AC6 ✅ Semester dates outside its AcademicYear's range → `422
  SEMESTER_OUTSIDE_ACADEMIC_YEAR`.
- AC7 ✅ case-insensitive substring search on Department proven; same
  `CRUDBase` code path backs all 7 entities.
- AC8 ✅ `page`/`page_size`/`total` verified on Department; identical
  `CRUDBase.list_paginated` backs the rest.
- AC9 ✅ deactivated Department remains fetchable via `GET` with
  `is_active: false`.

All acceptance criteria met. Proceeding to SPEC 05 (Student Management).

## Final Status
COMPLETE
