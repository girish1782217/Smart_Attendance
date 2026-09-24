from app.core.roles import RoleName


def _login_headers(client, email, password):
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _setup(client, admin_headers):
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
    subject1 = client.post(
        "/api/v1/subjects",
        json={"name": "Data Structures", "code": "CS201", "department_id": dept["id"]},
        headers=admin_headers,
    ).json()
    subject2 = client.post(
        "/api/v1/subjects",
        json={"name": "Algorithms", "code": "CS202", "department_id": dept["id"]},
        headers=admin_headers,
    ).json()
    faculty1 = client.post(
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
    faculty2 = client.post(
        "/api/v1/faculty",
        json={
            "email": "faculty2@example.com",
            "full_name": "Dr. Bob Faculty",
            "password": "faculty-password-123",
            "employee_id": "EMP002",
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
            "faculty_id": faculty1["id"],
            "subject_id": subject1["id"],
            "section_id": section["id"],
            "semester_id": semester["id"],
        },
        headers=admin_headers,
    )
    client.post(
        "/api/v1/faculty-assignments",
        json={
            "faculty_id": faculty2["id"],
            "subject_id": subject2["id"],
            "section_id": section["id"],
            "semester_id": semester["id"],
        },
        headers=admin_headers,
    )
    student = client.post(
        "/api/v1/students",
        json={
            "email": "student1@example.com",
            "full_name": "Alice Student",
            "password": "student-password-123",
            "roll_number": "R1",
            "section_id": section["id"],
        },
        headers=admin_headers,
    ).json()
    return {
        "section": section,
        "subject1": subject1,
        "subject2": subject2,
        "faculty1": faculty1,
        "faculty2": faculty2,
        "student": student,
    }


def _mark_and_submit(client, admin_headers, *, faculty_id, subject_id, section_id, student_id, session_date, status):
    session = client.post(
        "/api/v1/attendance-sessions",
        json={
            "faculty_id": faculty_id,
            "subject_id": subject_id,
            "section_id": section_id,
            "session_date": session_date,
            "start_time": "09:00:00",
            "end_time": "10:00:00",
        },
        headers=admin_headers,
    ).json()
    client.put(
        f"/api/v1/attendance-sessions/{session['id']}/records",
        json={"records": [{"student_id": student_id, "status": status}]},
        headers=admin_headers,
    )
    client.post(f"/api/v1/attendance-sessions/{session['id']}/submit", headers=admin_headers)
    return session


def test_summary_computes_overall_and_per_subject_percentages(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student_id = ctx["student"]["id"]

    # subject1: PRESENT, ABSENT -> 50%
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty1"]["id"], subject_id=ctx["subject1"]["id"],
        section_id=ctx["section"]["id"], student_id=student_id, session_date="2025-08-01", status="PRESENT",
    )
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty1"]["id"], subject_id=ctx["subject1"]["id"],
        section_id=ctx["section"]["id"], student_id=student_id, session_date="2025-08-02", status="ABSENT",
    )
    # subject2: PRESENT, PRESENT -> 100%
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty2"]["id"], subject_id=ctx["subject2"]["id"],
        section_id=ctx["section"]["id"], student_id=student_id, session_date="2025-08-03", status="PRESENT",
    )
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty2"]["id"], subject_id=ctx["subject2"]["id"],
        section_id=ctx["section"]["id"], student_id=student_id, session_date="2025-08-04", status="PRESENT",
    )

    response = client.get(f"/api/v1/students/{student_id}/attendance-summary", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    # overall: 3 present out of 4 -> 75%
    assert body["overall"]["percentage"] == 75.0
    by_subject = {row["subject_code"]: row for row in body["by_subject"]}
    assert by_subject["CS201"]["percentage"] == 50.0
    assert by_subject["CS202"]["percentage"] == 100.0


def test_summary_with_no_records_returns_null_percentage(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)

    response = client.get(
        f"/api/v1/students/{ctx['student']['id']}/attendance-summary", headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json()["overall"]["percentage"] is None
    assert response.json()["by_subject"] == []


def test_history_filters_by_subject_and_date_range(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student_id = ctx["student"]["id"]
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty1"]["id"], subject_id=ctx["subject1"]["id"],
        section_id=ctx["section"]["id"], student_id=student_id, session_date="2025-08-01", status="PRESENT",
    )
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty2"]["id"], subject_id=ctx["subject2"]["id"],
        section_id=ctx["section"]["id"], student_id=student_id, session_date="2025-09-01", status="ABSENT",
    )

    by_subject = client.get(
        f"/api/v1/students/{student_id}/attendance-history?subject_id={ctx['subject1']['id']}",
        headers=admin_headers,
    ).json()
    assert by_subject["total"] == 1
    assert by_subject["items"][0]["subject_code"] == "CS201"

    by_date = client.get(
        f"/api/v1/students/{student_id}/attendance-history?from_date=2025-08-15&to_date=2025-09-30",
        headers=admin_headers,
    ).json()
    assert by_date["total"] == 1
    assert by_date["items"][0]["session_date"] == "2025-09-01"


def test_corrected_record_shows_current_status_and_correction_detail(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student_id = ctx["student"]["id"]
    session = _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty1"]["id"], subject_id=ctx["subject1"]["id"],
        section_id=ctx["section"]["id"], student_id=student_id, session_date="2025-08-01", status="ABSENT",
    )
    record = client.get(
        f"/api/v1/attendance-sessions/{session['id']}/records", headers=admin_headers
    ).json()[0]
    student_headers = _login_headers(client, ctx["student"]["email"], "student-password-123")
    correction = client.post(
        f"/api/v1/attendance-records/{record['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "I was there."},
        headers=student_headers,
    ).json()
    client.post(f"/api/v1/corrections/{correction['id']}/approve", json={}, headers=admin_headers)

    response = client.get(
        f"/api/v1/students/{student_id}/attendance-history", headers=admin_headers
    )

    item = response.json()["items"][0]
    assert item["status"] == "PRESENT"
    assert item["was_corrected"] is True
    assert item["correction"]["original_status"] == "ABSENT"
    assert item["correction"]["approved_status"] == "PRESENT"


def test_student_cannot_view_another_students_history(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    other_student = client.post(
        "/api/v1/students",
        json={
            "email": "other-student@example.com",
            "full_name": "Bob Student",
            "password": "student-password-123",
            "roll_number": "R2",
            "section_id": ctx["section"]["id"],
        },
        headers=admin_headers,
    ).json()
    other_student_headers = _login_headers(client, other_student["email"], "student-password-123")

    response = client.get(
        f"/api/v1/students/{ctx['student']['id']}/attendance-summary", headers=other_student_headers
    )

    assert response.status_code == 403


def test_student_role_with_no_linked_profile_gets_404(client, make_auth_headers):
    """A STUDENT-role user provisioned generically (e.g. via POST
    /api/v1/users, bypassing student_service's create flow) has no linked
    Student row — a documented edge case, not a bug (mirrors SPEC 06's
    FACULTY_PROFILE_NOT_FOUND handling)."""
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    bare_student_headers = make_auth_headers([RoleName.STUDENT])

    response = client.get(
        f"/api/v1/students/{ctx['student']['id']}/attendance-summary", headers=bare_student_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "STUDENT_PROFILE_NOT_FOUND"


def test_student_can_view_own_history(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student_headers = _login_headers(client, ctx["student"]["email"], "student-password-123")

    response = client.get(
        f"/api/v1/students/{ctx['student']['id']}/attendance-summary", headers=student_headers
    )

    assert response.status_code == 200


def test_faculty_summary_scoped_to_own_subject_only(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student_id = ctx["student"]["id"]
    # faculty1 teaches subject1: mark ABSENT (would be 0%)
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty1"]["id"], subject_id=ctx["subject1"]["id"],
        section_id=ctx["section"]["id"], student_id=student_id, session_date="2025-08-01", status="ABSENT",
    )
    # faculty2 teaches subject2: mark PRESENT (would be 100%) -- faculty1 must not see this.
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty2"]["id"], subject_id=ctx["subject2"]["id"],
        section_id=ctx["section"]["id"], student_id=student_id, session_date="2025-08-02", status="PRESENT",
    )

    faculty1_headers = _login_headers(client, ctx["faculty1"]["email"], "faculty-password-123")
    response = client.get(
        f"/api/v1/students/{student_id}/attendance-summary", headers=faculty1_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["overall"]["percentage"] == 0.0  # only faculty1's ABSENT record counted
    assert len(body["by_subject"]) == 1
    assert body["by_subject"][0]["subject_code"] == "CS201"
