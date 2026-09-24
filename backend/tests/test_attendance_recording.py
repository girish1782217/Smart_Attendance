from app.core.roles import RoleName


def _setup(client, admin_headers, num_students=3):
    dept = client.post(
        "/api/v1/departments", json={"name": "Computer Science", "code": "CSE"}, headers=admin_headers
    ).json()
    program = client.post(
        "/api/v1/programs",
        json={"name": "B.Tech CSE", "code": "BTCSE", "department_id": dept["id"]},
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
        json={"name": "Data Structures", "code": "CS201", "department_id": dept["id"]},
        headers=admin_headers,
    ).json()
    faculty = client.post(
        "/api/v1/faculty",
        json={
            "email": "faculty1@example.com",
            "full_name": "Dr. Jane Faculty",
            "password": "faculty-password-123",
            "employee_id": "EMP001",
            "department_id": dept["id"],
        },
        headers=admin_headers,
    ).json()
    year = client.post(
        "/api/v1/academic-years",
        json={"name": "2025-2026", "start_date": "2025-06-01", "end_date": "2026-05-31"},
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
    students = []
    for i in range(num_students):
        student = client.post(
            "/api/v1/students",
            json={
                "email": f"student{i}@example.com",
                "full_name": f"Student {i}",
                "password": "student-password-123",
                "roll_number": f"R{i}",
                "section_id": section["id"],
            },
            headers=admin_headers,
        ).json()
        students.append(student)
    session = client.post(
        "/api/v1/attendance-sessions",
        json={
            "faculty_id": faculty["id"],
            "subject_id": subject["id"],
            "section_id": section["id"],
            "session_date": "2025-08-01",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
        },
        headers=admin_headers,
    ).json()
    return {"section": section, "subject": subject, "faculty": faculty, "students": students, "session": session}


def test_mark_all_four_statuses(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=4)
    students = ctx["students"]

    response = client.put(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/records",
        json={
            "records": [
                {"student_id": students[0]["id"], "status": "PRESENT"},
                {"student_id": students[1]["id"], "status": "ABSENT"},
                {"student_id": students[2]["id"], "status": "LATE"},
                {"student_id": students[3]["id"], "status": "EXCUSED"},
            ]
        },
        headers=admin_headers,
    )

    assert response.status_code == 200
    statuses = {record["student_id"]: record["status"] for record in response.json()}
    assert statuses[students[0]["id"]] == "PRESENT"
    assert statuses[students[1]["id"]] == "ABSENT"
    assert statuses[students[2]["id"]] == "LATE"
    assert statuses[students[3]["id"]] == "EXCUSED"


def test_resaving_updates_existing_record_upsert(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=1)
    student_id = ctx["students"][0]["id"]
    session_id = ctx["session"]["id"]

    client.put(
        f"/api/v1/attendance-sessions/{session_id}/records",
        json={"records": [{"student_id": student_id, "status": "ABSENT"}]},
        headers=admin_headers,
    )
    response = client.put(
        f"/api/v1/attendance-sessions/{session_id}/records",
        json={"records": [{"student_id": student_id, "status": "PRESENT"}]},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "PRESENT"

    records = client.get(
        f"/api/v1/attendance-sessions/{session_id}/records", headers=admin_headers
    ).json()
    assert len(records) == 1  # upsert, not a second row


def test_marking_student_not_in_roster_returns_404(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=1)

    response = client.put(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/records",
        json={"records": [{"student_id": 999999, "status": "PRESENT"}]},
        headers=admin_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "STUDENT_NOT_IN_ROSTER"


def test_faculty_who_does_not_own_session_gets_403(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=1)

    dept_list = client.get("/api/v1/departments", headers=admin_headers).json()["items"]
    other_faculty = client.post(
        "/api/v1/faculty",
        json={
            "email": "other2@example.com",
            "full_name": "Dr. Other Two",
            "password": "faculty-password-123",
            "employee_id": "EMP998",
            "department_id": dept_list[0]["id"],
        },
        headers=admin_headers,
    ).json()
    other_login = client.post(
        "/api/v1/auth/login", json={"email": "other2@example.com", "password": "faculty-password-123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = client.put(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/records",
        json={"records": [{"student_id": ctx["students"][0]["id"], "status": "PRESENT"}]},
        headers=other_headers,
    )

    assert response.status_code == 403


def test_duplicate_student_in_same_request_returns_422(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=1)
    student_id = ctx["students"][0]["id"]

    response = client.put(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/records",
        json={
            "records": [
                {"student_id": student_id, "status": "PRESENT"},
                {"student_id": student_id, "status": "ABSENT"},
            ]
        },
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_submit_with_incomplete_roster_returns_409(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=2)
    # Mark only one of the two students.
    client.put(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/records",
        json={"records": [{"student_id": ctx["students"][0]["id"], "status": "PRESENT"}]},
        headers=admin_headers,
    )

    response = client.post(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/submit", headers=admin_headers
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INCOMPLETE_ROSTER"


def test_submit_with_complete_roster_succeeds(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=2)
    client.put(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/records",
        json={
            "records": [
                {"student_id": ctx["students"][0]["id"], "status": "PRESENT"},
                {"student_id": ctx["students"][1]["id"], "status": "ABSENT"},
            ]
        },
        headers=admin_headers,
    )

    response = client.post(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/submit", headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"


def test_double_submit_returns_409(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=1)
    client.put(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/records",
        json={"records": [{"student_id": ctx["students"][0]["id"], "status": "PRESENT"}]},
        headers=admin_headers,
    )
    client.post(f"/api/v1/attendance-sessions/{ctx['session']['id']}/submit", headers=admin_headers)

    response = client.post(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/submit", headers=admin_headers
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_ALREADY_SUBMITTED"


def test_marking_after_submission_is_rejected(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=1)
    student_id = ctx["students"][0]["id"]
    client.put(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/records",
        json={"records": [{"student_id": student_id, "status": "PRESENT"}]},
        headers=admin_headers,
    )
    client.post(f"/api/v1/attendance-sessions/{ctx['session']['id']}/submit", headers=admin_headers)

    response = client.put(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/records",
        json={"records": [{"student_id": student_id, "status": "ABSENT"}]},
        headers=admin_headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_ALREADY_SUBMITTED"


def test_student_role_forbidden_on_all_endpoints(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=1)
    student_headers = make_auth_headers([RoleName.STUDENT])
    session_id = ctx["session"]["id"]

    assert (
        client.put(
            f"/api/v1/attendance-sessions/{session_id}/records",
            json={"records": [{"student_id": ctx["students"][0]["id"], "status": "PRESENT"}]},
            headers=student_headers,
        ).status_code
        == 403
    )
    assert client.get(f"/api/v1/attendance-sessions/{session_id}/records", headers=student_headers).status_code == 403
    assert client.post(f"/api/v1/attendance-sessions/{session_id}/submit", headers=student_headers).status_code == 403
