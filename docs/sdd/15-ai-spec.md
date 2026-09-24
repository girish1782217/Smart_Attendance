# SPEC 15 — Gemini AI Insights

## Status
REMOVED (2026-09-25) — implemented and accepted per the record below (9/9
tests passing at the time), then fully removed at the user's explicit
request because the application is not using AI. All code
(`app/api/v1/ai_insights.py`, `app/schemas/ai_insight.py`,
`app/services/ai_insight_service.py`, `app/services/gemini_client.py`,
`get_gemini_generate_fn` in `app/api/deps.py`, the `gemini_*` settings in
`app/core/config.py`, and `tests/test_ai_insights.py`) and the corresponding
frontend page/route/nav item have been deleted. The rest of this document is
kept as a historical record of what was built and verified, not a
description of current behavior — see `docs/traceability-matrix.md` for the
current status.

## Objective
A backend-only Gemini integration that summarizes **already-computed**
attendance data in natural language. Gemini is advisory only — it never
computes, never stores, and never becomes a source of truth for attendance
numbers (Assumption A-8, brief §16–17).

## Design
- **No SDK dependency**: calls the Gemini REST API directly via `httpx`
  (already installed, used elsewhere in this codebase) rather than adding
  `google-generativeai`. This keeps the integration small, avoids a new
  dependency whose exact current API shape I can't fully verify against my
  training cutoff, and — most importantly — makes the call trivially
  mockable via dependency injection without needing the real package
  installed in the test environment at all.
- **Dependency-injected client**: `app/api/deps.py` gains
  `get_gemini_generate_fn()`, a FastAPI dependency returning
  `gemini_client.generate_content` by default. Tests override it via
  `app.dependency_overrides` with a fake function — no network access, no
  live API key, ever required for the test suite (explicit brief
  requirement).
- **Distinct exception types** (`app/services/gemini_client.py`) —
  `GeminiTimeoutError`, `GeminiProviderError` (non-2xx HTTP),
  `GeminiInvalidResponseError` (2xx but unparseable shape) — so the service
  layer can report *which* failure mode occurred, matching the brief's
  distinct test cases (timeout vs. invalid response vs. generic failure).
- **Graceful degradation, not request failure**: the endpoint always
  returns `200` with the deterministically-computed data
  (`AttendanceCounts`/subject breakdown — reusing SPEC 10's
  `attendance_history_service.get_summary` verbatim); `ai_available`,
  `insight_text`, and `ai_error_code` report whether the narrative
  succeeded. A missing API key, timeout, or provider error degrades the AI
  portion only — the numbers a caller needs are never withheld because
  Gemini is unavailable.
- **Data grounding**: the prompt embeds only the already-computed summary
  numbers, with explicit instructions (brief §16): use only the provided
  data, do not invent facts, do not modify records, do not decide on an
  admin's behalf, distinguish facts from suggestions. The API response's
  numeric fields are constructed independently of the AI call and can never
  be influenced by what Gemini returns — there is no code path where the
  model's text writes back into `overall`/`by_subject`.
- **Authorization/scoping**: identical to SPEC 10's attendance-summary
  endpoint (STUDENT own-only, FACULTY scoped to their own sessions, ADMIN
  unrestricted) — the scoping logic (`_resolve_faculty_scope` in
  `attendance_history.py`) is promoted to `scoping.py` as
  `resolve_student_access_scope`, now a shared second consumer.

## Requirements
- R1: `GET /students/{id}/ai-insight` — computes the summary, builds the
  grounded prompt, calls Gemini via the injected client, returns data +
  advisory text (or a graceful failure code).
- R2: Missing `GEMINI_API_KEY` → `ai_error_code: MISSING_API_KEY`, `200`,
  data still present.
- R3: Timeout / non-2xx / unparseable response → distinct `ai_error_code`s,
  same graceful `200` degradation.
- R4: Same role-scoping as SPEC 10.
- R5: The API key is never present in any response, log line, or error
  message.

## Acceptance Criteria
- AC1: A mocked successful Gemini call returns `ai_available: true` and the
  mocked text verbatim.
- AC2: Missing API key → `ai_available: false`, `ai_error_code:
  MISSING_API_KEY`, and the deterministic `overall`/`by_subject` data is
  still fully present and correct.
- AC3: A mocked timeout → `ai_error_code: TIMEOUT`.
- AC4: A mocked non-2xx response → `ai_error_code: PROVIDER_ERROR`.
- AC5: A mocked 2xx response with an unexpected JSON shape →
  `ai_error_code: INVALID_RESPONSE`.
- AC6: The response's `overall`/`by_subject` numbers are asserted equal to
  a hand-computed expectation regardless of what the mocked Gemini function
  returns — proving the AI text can never alter the numbers.
- AC7: STUDENT gets `403` requesting another student's insight; FACULTY
  scoped exactly like SPEC 10 AC5.
- AC8: No test in this suite makes a real network call — every Gemini
  interaction goes through the dependency override.

## Technical Design
- `app/services/gemini_client.py` (new) — `generate_content`,
  `GeminiError`/`GeminiTimeoutError`/`GeminiProviderError`/
  `GeminiInvalidResponseError`.
- `app/services/scoping.py`: add `resolve_student_access_scope` (extracted
  from `attendance_history.py`).
- `app/services/ai_insight_service.py` (new) — prompt building + graceful
  degradation logic.
- `app/api/deps.py`: add `get_gemini_generate_fn`.
- `app/schemas/ai_insight.py`.
- `app/api/v1/ai_insights.py`.

## Implementation
See files above; committed alongside this spec.

## Tests
`backend/tests/test_ai_insights.py`.

## Test Results
9 new tests in `backend/tests/test_ai_insights.py`, including one that
monkeypatches `httpx.post` to raise if ever called at all — a hard
guarantee this suite makes zero live network calls. Also re-ran SPEC 10's
`test_attendance_history.py` immediately after promoting the scoping helper
to `scoping.py`, before writing any new test, to confirm the refactor was
behavior-preserving (8/8 passed unmodified).

## Defects Found
One **test-infrastructure timing bug**, caught immediately by 5 of the 9
new tests failing on first run with `MISSING_API_KEY` instead of their
expected error code:

`get_settings()` is `lru_cache`'d. My first attempt cleared the cache in an
autouse fixture's setup phase (i.e., *before* the test function body runs)
expecting that to be enough. But the `client` fixture's own setup calls
`create_app()`, which calls `get_settings()` internally (via
`configure_logging()` and CORS middleware setup) — and pytest resolves
`client` fixture creation *after* my autouse fixture's pre-yield code but
*before* the test function body's `monkeypatch.setenv(...)` line executes.
So `create_app()` re-populated the cache with the real (empty)
`GEMINI_API_KEY` *after* my fixture cleared it but *before* the test ever
got to set the fake key — leaving a stale cached `Settings` object with the
wrong key for the rest of the test.

## Fixes Applied
Added an explicit `get_settings.cache_clear()` immediately after every
`monkeypatch.setenv("GEMINI_API_KEY", ...)` call within each test body,
guaranteeing the clear happens *after* the env var is actually set and
*before* the request that depends on it. The autouse fixture's pre-test and
post-test clears are kept as well, for general hygiene and to prevent any
stale cache leaking into unrelated tests in other files.

## Regression Results
Full backend suite (`pytest -q`, from `backend/`): **158 passed** (149 from
SPEC 01–14 + 9 new). No regressions.

## Acceptance Verification
- AC1 ✅ mocked success returns the mocked text verbatim, `ai_available: true`.
- AC2 ✅ empty `GEMINI_API_KEY` → `ai_error_code: MISSING_API_KEY`, `200`,
  with `overall.percentage` still correctly computed and present.
- AC3–AC5 ✅ `GeminiTimeoutError`/`GeminiProviderError`/
  `GeminiInvalidResponseError` each map to their own distinct
  `ai_error_code` (`TIMEOUT`/`PROVIDER_ERROR`/`INVALID_RESPONSE`).
- AC6 ✅ a mocked Gemini response that explicitly claims a false percentage
  ("100%, never missed a class") is returned in `insight_text` as-is, while
  `overall.percentage` still correctly reports the real `0.0` — proving the
  numeric fields are structurally incapable of being influenced by the
  model's text.
- AC7 ✅ a genuine second student gets `403`; a faculty member with no
  assignment to the student's section sees `percentage: null` (zero records
  in scope), matching SPEC 10's exact scoping behavior.
- AC8 ✅ `test_no_network_call_is_ever_made` monkeypatches `httpx.post` to
  raise `AssertionError` if invoked, and the request still succeeds via the
  injected mock — proof this and every other test in the file never touches
  the network.

All acceptance criteria met. Proceeding to SPEC 16 (Security Hardening).

## Final Status
COMPLETE
