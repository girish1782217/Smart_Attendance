from app.core.roles import RoleName


def _full_hierarchy(client, headers, dept_code="CSE"):
    dept = client.post(
        "/api/v1/departments", json={"name": f"Dept {dept_code}", "code": dept_code}, headers=headers
    ).json()
    program = client.post(
        "/api/v1/programs",
        json={"name": f"Program {dept_code}", "code": f"P{dept_code}", "department_id": dept["id"]},
        headers=headers,
    ).json()
    academic_class = client.post(
        "/api/v1/classes", json={"name": "First Year", "program_id": program["id"]}, headers=headers
    ).json()
    section = client.post(
        "/api/v1/sections", json={"name": "A", "class_id": academic_class["id"]}, headers=headers
    ).json()
    subject = client.post(
        "/api/v1/subjects",
        json={"name": "Data Structures", "code": f"CS{dept_code}", "department_id": dept["id"]},
        headers=headers,
    ).json()
    return {"department": dept, "section": section, "subject": subject}


def _create_faculty(client, headers, department_id, email="faculty1@example.com", employee_id="EMP001"):
    return client.post(
        "/api/v1/faculty",
        json={
            "email": email,
            "full_name": "Dr. Jane Faculty",
            "password": "faculty-password-123",
            "employee_id": employee_id,
            "department_id": department_id,
        },
        headers=headers,
    ).json()


def _assign(client, headers, *, faculty_id, subject_id, section_id, semester_id):
    return client.post(
        "/api/v1/faculty-assignments",
        json={
            "faculty_id": faculty_id,
            "subject_id": subject_id,
            "section_id": section_id,
            "semester_id": semester_id,
        },
        headers=headers,
    ).json()


def _create_semester(client, headers):
    year = client.post(
        "/api/v1/academic-years",
        json={"name": "2025-2026", "start_date": "2025-06-01", "end_date": "2026-05-31"},
        headers=headers,
    ).json()
    return client.post(
        "/api/v1/semesters",
        json={
            "name": "Semester 1",
            "academic_year_id": year["id"],
            "start_date": "2025-06-01",
            "end_date": "2025-11-30",
        },
        headers=headers,
    ).json()


def _setup_assigned_faculty(client, admin_headers):
    ctx = _full_hierarchy(client, admin_headers)
    faculty = _create_faculty(client, admin_headers, ctx["department"]["id"])
    semester = _create_semester(client, admin_headers)
    _assign(
        client,
        admin_headers,
        faculty_id=faculty["id"],
        subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"],
        semester_id=semester["id"],
    )
    return {**ctx, "faculty": faculty, "semester": semester}


def _session_payload(ctx, faculty_id=None, session_date="2025-08-01", start="09:00:00", end="10:00:00"):
    payload = {
        "subject_id": ctx["subject"]["id"],
        "section_id": ctx["section"]["id"],
        "session_date": session_date,
        "start_time": start,
        "end_time": end,
    }
    if faculty_id is not None:
        payload["faculty_id"] = faculty_id
    return payload


def test_admin_creates_session_for_assigned_faculty(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_assigned_faculty(client, admin_headers)

    response = client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(ctx, faculty_id=ctx["faculty"]["id"]),
        headers=admin_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "SCHEDULED"
    assert body["faculty_id"] == ctx["faculty"]["id"]
    assert body["subject_name"] == "Data Structures"
    assert body["section_name"] == "A"


def test_admin_without_faculty_id_gets_422(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_assigned_faculty(client, admin_headers)

    response = client.post(
        "/api/v1/attendance-sessions", json=_session_payload(ctx), headers=admin_headers
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "FACULTY_ID_REQUIRED"


def test_faculty_creates_own_session_ignoring_supplied_faculty_id(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_assigned_faculty(client, admin_headers)
    faculty_login = client.post(
        "/api/v1/auth/login",
        json={"email": "faculty1@example.com", "password": "faculty-password-123"},
    )
    faculty_headers = {"Authorization": f"Bearer {faculty_login.json()['access_token']}"}

    response = client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(ctx, faculty_id=999999),  # bogus id, must be ignored
        headers=faculty_headers,
    )

    assert response.status_code == 201
    assert response.json()["faculty_id"] == ctx["faculty"]["id"]


def test_create_session_with_invalid_subject_returns_404(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_assigned_faculty(client, admin_headers)
    payload = _session_payload(ctx, faculty_id=ctx["faculty"]["id"])
    payload["subject_id"] = 999

    response = client.post("/api/v1/attendance-sessions", json=payload, headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SUBJECT_NOT_FOUND"


def test_create_session_for_unassigned_faculty_returns_403(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _full_hierarchy(client, admin_headers)
    # Faculty created but never assigned to this subject/section.
    faculty = _create_faculty(client, admin_headers, ctx["department"]["id"])

    response = client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(ctx, faculty_id=faculty["id"]),
        headers=admin_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FACULTY_NOT_ASSIGNED"


def test_overlapping_session_returns_409(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_assigned_faculty(client, admin_headers)
    client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(ctx, faculty_id=ctx["faculty"]["id"], start="09:00:00", end="10:00:00"),
        headers=admin_headers,
    )

    response = client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(ctx, faculty_id=ctx["faculty"]["id"], start="09:30:00", end="10:30:00"),
        headers=admin_headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_TIME_OVERLAP"


def test_non_overlapping_back_to_back_sessions_succeed(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_assigned_faculty(client, admin_headers)
    client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(ctx, faculty_id=ctx["faculty"]["id"], start="09:00:00", end="10:00:00"),
        headers=admin_headers,
    )

    response = client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(ctx, faculty_id=ctx["faculty"]["id"], start="10:00:00", end="11:00:00"),
        headers=admin_headers,
    )

    assert response.status_code == 201


def test_end_time_before_start_time_returns_422(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_assigned_faculty(client, admin_headers)

    response = client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(ctx, faculty_id=ctx["faculty"]["id"], start="10:00:00", end="09:00:00"),
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_student_forbidden_on_all_session_endpoints(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_assigned_faculty(client, admin_headers)
    created = client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(ctx, faculty_id=ctx["faculty"]["id"]),
        headers=admin_headers,
    ).json()

    student_headers = make_auth_headers([RoleName.STUDENT])
    assert client.get("/api/v1/attendance-sessions", headers=student_headers).status_code == 403
    assert (
        client.get(f"/api/v1/attendance-sessions/{created['id']}", headers=student_headers).status_code
        == 403
    )
    assert (
        client.post("/api/v1/attendance-sessions", json=_session_payload(ctx), headers=student_headers).status_code
        == 403
    )


def test_faculty_cannot_access_another_facultys_session(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_assigned_faculty(client, admin_headers)
    created = client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(ctx, faculty_id=ctx["faculty"]["id"]),
        headers=admin_headers,
    ).json()

    other_faculty = _create_faculty(
        client, admin_headers, ctx["department"]["id"], email="other@example.com", employee_id="EMP999"
    )
    other_login = client.post(
        "/api/v1/auth/login", json={"email": "other@example.com", "password": "faculty-password-123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    get_response = client.get(f"/api/v1/attendance-sessions/{created['id']}", headers=other_headers)
    roster_response = client.get(
        f"/api/v1/attendance-sessions/{created['id']}/roster", headers=other_headers
    )
    list_response = client.get("/api/v1/attendance-sessions", headers=other_headers)

    assert get_response.status_code == 403
    assert roster_response.status_code == 403
    assert list_response.json()["total"] == 0


def test_roster_returns_active_students_in_section(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_assigned_faculty(client, admin_headers)
    for i in range(2):
        client.post(
            "/api/v1/students",
            json={
                "email": f"student{i}@example.com",
                "full_name": f"Student {i}",
                "password": "student-password-123",
                "roll_number": f"R{i}",
                "section_id": ctx["section"]["id"],
            },
            headers=admin_headers,
        )
    created = client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(ctx, faculty_id=ctx["faculty"]["id"]),
        headers=admin_headers,
    ).json()

    response = client.get(f"/api/v1/attendance-sessions/{created['id']}/roster", headers=admin_headers)

    assert response.status_code == 200
    roll_numbers = {student["roll_number"] for student in response.json()}
    assert roll_numbers == {"R0", "R1"}


def test_list_sessions_filters_by_date_range(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_assigned_faculty(client, admin_headers)
    client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(ctx, faculty_id=ctx["faculty"]["id"], session_date="2025-08-01"),
        headers=admin_headers,
    )
    client.post(
        "/api/v1/attendance-sessions",
        json=_session_payload(
            ctx, faculty_id=ctx["faculty"]["id"], session_date="2025-09-01", start="11:00:00", end="12:00:00"
        ),
        headers=admin_headers,
    )

    response = client.get(
        "/api/v1/attendance-sessions?from_date=2025-08-15&to_date=2025-09-30", headers=admin_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["session_date"] == "2025-09-01"
