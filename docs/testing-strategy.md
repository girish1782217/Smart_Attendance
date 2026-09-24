# Testing Strategy

## Pyramid

```text
                E2E (Playwright)
                6 required workflows
             /----------------------\
          Integration (pytest + FastAPI TestClient,
          Vitest + RTL for frontend components)
       /--------------------------------------------\
     Unit (pure functions: attendance %, threshold checks,
     validators; service-layer logic with a real test DB per test)
```

## Backend

- **Framework**: pytest + pytest-asyncio (where async code is exercised).
- **DB isolation**: each test function gets a fresh SQLite file (or
  in-memory `sqlite:///:memory:` with `StaticPool`) via a fixture that creates
  all tables, yields a session, and tears down — no cross-test state leakage.
- **Auth in tests**: fixtures create users per role and return a valid bearer
  token via the real login endpoint (not a bypass), so authz is exercised
  honestly.
- **External services**: Gemini is mocked via dependency override
  (`app.dependency_overrides`) — no test depends on live network access.
- **Naming**: `backend/tests/test_<spec_area>.py`, one file per spec.
- **Coverage expectation**: every service branch (happy path + each declared
  edge case in the spec) has an assertion.

## Frontend

- **Framework**: Vitest + React Testing Library.
- Component tests cover: rendering, user interaction (forms, filters,
  pagination), loading/error/empty states, and role-based conditional
  rendering (as a UX check — never the security boundary).
- API calls are mocked (msw or vi.mock) — no frontend test hits a real
  backend.

## E2E

- **Framework**: Playwright, against the real backend (SQLite test DB) and
  built frontend.
- Covers the six required workflows from `00-product-spec.md` §3 exactly as
  named acceptance scenarios.
- Seed data is reset before the E2E run via a dedicated seed script.

## Regression discipline

Per the SDD process: after implementing spec N, run:
1. `pytest` (full backend suite)
2. `npm test` (full frontend suite, once frontend exists)
3. Relevant `npx playwright test` subset (once E2E exists)

A spec is marked COMPLETE only when its own tests pass **and** the full
existing suite still passes. Results are recorded in the spec's own
`## Test Results` / `## Regression Results` sections and rolled into
`traceability-matrix.md`.
