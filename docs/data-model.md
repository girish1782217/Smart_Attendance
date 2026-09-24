# Data Model

> This document is filled in incrementally as each spec introduces entities.
> SPEC-01 introduces no persistent entities (health check only). Entity
> definitions begin at `04-master-data-spec.md`.

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
| _(none yet)_ | | |
