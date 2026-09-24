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
