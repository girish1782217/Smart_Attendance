import pytest

from app.api.deps import get_gemini_generate_fn
from app.core.config import get_settings
from app.core.roles import RoleName
from app.services.gemini_client import (
    GeminiInvalidResponseError,
    GeminiProviderError,
    GeminiTimeoutError,
)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """get_settings() is lru_cache'd; several tests here monkeypatch
    GEMINI_API_KEY, so the cache must be cleared both before (to pick up
    the patched value) and after (so monkeypatch's teardown restoring the
    real env isn't masked by a stale cached Settings instance leaking into
    a later test)."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _login_headers(client, email, password):
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _setup(client, admin_headers, dept_name="Computer Science", dept_code="CSE"):
    dept = client.post(
        "/api/v1/departments", json={"name": dept_name, "code": dept_code}, headers=admin_headers
    ).json()
    program = client.post(
        "/api/v1/programs",
        json={"name": f"Program {dept_code}", "code": f"P{dept_code}", "department_id": dept["id"]},
        headers=admin_headers,
    ).json()
    academic_class = client.post(
        "/api/v1/classes", json={"name": "First Year", "program_id": program["id"]}, headers=admin_headers
    ).json()
    section = client.post(
        "/api/v1/sections", json={"name": "A", "class_id": academic_class["id"]}, headers=admin_headers
    ).json()
    subject = client.post(
        "/api/v1/subjects",
        json={"name": "Data Structures", "code": f"CS{dept_code}", "department_id": dept["id"]},
        headers=admin_headers,
    ).json()
    faculty = client.post(
        "/api/v1/faculty",
        json={
            "email": f"faculty-{dept_code}@example.com",
            "full_name": "Dr. Jane Faculty",
            "password": "faculty-password-123",
            "employee_id": f"EMP-{dept_code}",
            "department_id": dept["id"],
        },
        headers=admin_headers,
    ).json()
    year = client.post(
        "/api/v1/academic-years",
        json={"name": f"2025-2026-{dept_code}", "start_date": "2025-06-01", "end_date": "2026-05-31"},
        headers=admin_headers,
    ).json()
    semester = client.post(
        "/api/v1/semesters",
        json={
            "name": "Semester 1",
            "academic_year_id": year["id"],
            "start_date": "2025-06-01",
            "end_date": "2025-11-30",
        },
        headers=admin_headers,
    ).json()
    client.post(
        "/api/v1/faculty-assignments",
        json={
            "faculty_id": faculty["id"],
            "subject_id": subject["id"],
            "section_id": section["id"],
            "semester_id": semester["id"],
        },
        headers=admin_headers,
    )
    return {"department": dept, "section": section, "subject": subject, "faculty": faculty}


def _create_student(client, admin_headers, section_id, email, roll_number):
    return client.post(
        "/api/v1/students",
        json={
            "email": email,
            "full_name": f"Student {roll_number}",
            "password": "student-password-123",
            "roll_number": roll_number,
            "section_id": section_id,
        },
        headers=admin_headers,
    ).json()


def _mark_and_submit(client, admin_headers, *, faculty_id, subject_id, section_id, student_id, status, date_str):
    session = client.post(
        "/api/v1/attendance-sessions",
        json={
            "faculty_id": faculty_id, "subject_id": subject_id, "section_id": section_id,
            "session_date": date_str, "start_time": "09:00:00", "end_time": "10:00:00",
        },
        headers=admin_headers,
    ).json()
    client.put(
        f"/api/v1/attendance-sessions/{session['id']}/records",
        json={"records": [{"student_id": student_id, "status": status}]},
        headers=admin_headers,
    )
    client.post(f"/api/v1/attendance-sessions/{session['id']}/submit", headers=admin_headers)


def _override_gemini(client, fn):
    client.app.dependency_overrides[get_gemini_generate_fn] = lambda: fn


def test_successful_insight_returns_mocked_text_verbatim(client, make_auth_headers, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    get_settings.cache_clear()
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "s1@example.com", "R1")
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], status="PRESENT", date_str="2025-08-01",
    )
    _override_gemini(client, lambda prompt: "This student has excellent attendance.")

    response = client.get(f"/api/v1/students/{student['id']}/ai-insight", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["ai_available"] is True
    assert body["insight_text"] == "This student has excellent attendance."
    assert body["ai_error_code"] is None


def test_missing_api_key_degrades_gracefully_but_keeps_data(client, make_auth_headers, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "s2@example.com", "R2")
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], status="ABSENT", date_str="2025-08-01",
    )

    response = client.get(f"/api/v1/students/{student['id']}/ai-insight", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["ai_available"] is False
    assert body["ai_error_code"] == "MISSING_API_KEY"
    assert body["insight_text"] is None
    assert body["overall"]["percentage"] == 0.0  # data still fully present


def test_timeout_reported_as_distinct_error_code(client, make_auth_headers, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    get_settings.cache_clear()
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "s3@example.com", "R3")

    def _raise_timeout(prompt):
        raise GeminiTimeoutError("timed out")

    _override_gemini(client, _raise_timeout)

    response = client.get(f"/api/v1/students/{student['id']}/ai-insight", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["ai_error_code"] == "TIMEOUT"
    assert response.json()["ai_available"] is False


def test_provider_error_reported_as_distinct_error_code(client, make_auth_headers, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    get_settings.cache_clear()
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "s4@example.com", "R4")

    def _raise_provider_error(prompt):
        raise GeminiProviderError("HTTP 500")

    _override_gemini(client, _raise_provider_error)

    response = client.get(f"/api/v1/students/{student['id']}/ai-insight", headers=admin_headers)

    assert response.json()["ai_error_code"] == "PROVIDER_ERROR"


def test_invalid_response_reported_as_distinct_error_code(client, make_auth_headers, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    get_settings.cache_clear()
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "s5@example.com", "R5")

    def _raise_invalid(prompt):
        raise GeminiInvalidResponseError("bad shape")

    _override_gemini(client, _raise_invalid)

    response = client.get(f"/api/v1/students/{student['id']}/ai-insight", headers=admin_headers)

    assert response.json()["ai_error_code"] == "INVALID_RESPONSE"


def test_ai_text_cannot_alter_the_deterministic_numbers(client, make_auth_headers, monkeypatch):
    """Data grounding: even if the mocked Gemini response contains numbers
    that contradict the real data, the response's overall/by_subject fields
    must reflect only the deterministic calculation."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    get_settings.cache_clear()
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "s6@example.com", "R6")
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], status="ABSENT", date_str="2025-08-01",
    )

    _override_gemini(
        client, lambda prompt: "Your attendance is actually 100% and you have never missed a class."
    )

    response = client.get(f"/api/v1/students/{student['id']}/ai-insight", headers=admin_headers)

    assert response.status_code == 200
    # The real, deterministic number -- unaffected by what the AI text claims.
    assert response.json()["overall"]["percentage"] == 0.0


def test_no_network_call_is_ever_made(client, make_auth_headers, monkeypatch):
    """Proves this suite never depends on a live Gemini API: forcing
    httpx.post to raise if called at all."""
    import httpx

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("A real network call was attempted during tests.")

    monkeypatch.setattr(httpx, "post", _fail_if_called)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    get_settings.cache_clear()

    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "s7@example.com", "R7")
    _override_gemini(client, lambda prompt: "Mocked, no network involved.")

    response = client.get(f"/api/v1/students/{student['id']}/ai-insight", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["insight_text"] == "Mocked, no network involved."


def test_student_cannot_request_another_students_insight(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    target = _create_student(client, admin_headers, ctx["section"]["id"], "target@example.com", "T1")
    other = _create_student(client, admin_headers, ctx["section"]["id"], "other@example.com", "T2")
    other_headers = _login_headers(client, other["email"], "student-password-123")

    response = client.get(f"/api/v1/students/{target['id']}/ai-insight", headers=other_headers)

    assert response.status_code == 403


def test_faculty_scoped_insight_matches_history_scoping(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx1 = _setup(client, admin_headers, "Computer Science", "CSE")
    ctx2 = _setup(client, admin_headers, "Electronics", "ECE")
    student = _create_student(client, admin_headers, ctx1["section"]["id"], "multi@example.com", "M1")
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx1["faculty"]["id"], subject_id=ctx1["subject"]["id"],
        section_id=ctx1["section"]["id"], student_id=student["id"], status="ABSENT", date_str="2025-08-01",
    )

    ctx2_faculty_headers = _login_headers(client, ctx2["faculty"]["email"], "faculty-password-123")
    response = client.get(f"/api/v1/students/{student['id']}/ai-insight", headers=ctx2_faculty_headers)

    assert response.status_code == 200
    # ctx2's faculty doesn't teach this student -> zero records in scope.
    assert response.json()["overall"]["percentage"] is None
