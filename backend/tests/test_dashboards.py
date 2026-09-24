from app.core.roles import RoleName


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
    return {
        "department": dept,
        "class": academic_class,
        "section": section,
        "subject": subject,
        "faculty": faculty,
    }


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


def _mark_and_submit(
    client, admin_headers, *, faculty_id, subject_id, section_id, student_id, status, date_str,
    other_student_ids=(),
):
    session = client.post(
        "/api/v1/attendance-sessions",
        json={
            "faculty_id": faculty_id, "subject_id": subject_id, "section_id": section_id,
            "session_date": date_str, "start_time": "09:00:00", "end_time": "10:00:00",
        },
        headers=admin_headers,
    ).json()
    records = [{"student_id": student_id, "status": status}]
    records += [{"student_id": other_id, "status": "PRESENT"} for other_id in other_student_ids]
    client.put(
        f"/api/v1/attendance-sessions/{session['id']}/records", json={"records": records}, headers=admin_headers,
    )
    client.post(f"/api/v1/attendance-sessions/{session['id']}/submit", headers=admin_headers)
    return session


def test_role_exclusivity_across_all_three_dashboards(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    faculty_headers = _login_headers(client, ctx["faculty"]["email"], "faculty-password-123")
    student = _create_student(client, admin_headers, ctx["section"]["id"], "s@example.com", "R1")
    student_headers = _login_headers(client, student["email"], "student-password-123")

    assert client.get("/api/v1/dashboard/admin", headers=admin_headers).status_code == 200
    assert client.get("/api/v1/dashboard/admin", headers=faculty_headers).status_code == 403
    assert client.get("/api/v1/dashboard/admin", headers=student_headers).status_code == 403

    assert client.get("/api/v1/dashboard/faculty", headers=faculty_headers).status_code == 200
    assert client.get("/api/v1/dashboard/faculty", headers=admin_headers).status_code == 403
    assert client.get("/api/v1/dashboard/faculty", headers=student_headers).status_code == 403

    assert client.get("/api/v1/dashboard/student", headers=student_headers).status_code == 200
    assert client.get("/api/v1/dashboard/student", headers=admin_headers).status_code == 403
    assert client.get("/api/v1/dashboard/student", headers=faculty_headers).status_code == 403


def test_admin_dashboard_counts_match_scenario(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    _create_student(client, admin_headers, ctx["section"]["id"], "a@example.com", "A1")
    _create_student(client, admin_headers, ctx["section"]["id"], "b@example.com", "A2")

    response = client.get("/api/v1/dashboard/admin", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_students"] == 2
    assert body["total_faculty"] == 1
    assert body["total_departments"] == 1
    assert body["total_classes"] == 1
    assert body["pending_correction_requests"] == 0


def test_faculty_dashboard_low_attendance_scoped_to_own_sessions(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx1 = _setup(client, admin_headers, "Computer Science", "CSE")
    ctx2 = _setup(client, admin_headers, "Electronics", "ECE")
    student1 = _create_student(client, admin_headers, ctx1["section"]["id"], "s1@example.com", "S1")
    student2 = _create_student(client, admin_headers, ctx2["section"]["id"], "s2@example.com", "S2")
    # faculty1's student is below threshold; faculty2's student is fine.
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx1["faculty"]["id"], subject_id=ctx1["subject"]["id"],
        section_id=ctx1["section"]["id"], student_id=student1["id"], status="ABSENT", date_str="2025-08-01",
    )
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx2["faculty"]["id"], subject_id=ctx2["subject"]["id"],
        section_id=ctx2["section"]["id"], student_id=student2["id"], status="PRESENT", date_str="2025-08-01",
    )

    faculty1_headers = _login_headers(client, ctx1["faculty"]["email"], "faculty-password-123")
    response = client.get("/api/v1/dashboard/faculty", headers=faculty1_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["students_below_threshold"] == 1
    assert body["assigned_sections"] == 1
    assert body["total_sessions"] == 1


def test_student_dashboard_recent_attendance_capped_at_five(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "many@example.com", "M1")
    for i in range(7):
        _mark_and_submit(
            client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
            section_id=ctx["section"]["id"], student_id=student["id"], status="PRESENT",
            date_str=f"2025-08-{i + 1:02d}",
        )
    student_headers = _login_headers(client, student["email"], "student-password-123")

    response = client.get("/api/v1/dashboard/student", headers=student_headers)

    assert response.status_code == 200
    assert len(response.json()["recent_attendance"]) == 5


def test_student_dashboard_low_attendance_flag(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    below = _create_student(client, admin_headers, ctx["section"]["id"], "below@example.com", "B1")
    above = _create_student(client, admin_headers, ctx["section"]["id"], "above@example.com", "B2")
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=below["id"], status="ABSENT", date_str="2025-08-01",
        other_student_ids=[above["id"]],
    )

    below_headers = _login_headers(client, below["email"], "student-password-123")
    above_headers = _login_headers(client, above["email"], "student-password-123")

    below_response = client.get("/api/v1/dashboard/student", headers=below_headers).json()
    above_response = client.get("/api/v1/dashboard/student", headers=above_headers).json()

    assert below_response["is_low_attendance"] is True
    assert below_response["overall"]["percentage"] == 0.0
    assert above_response["is_low_attendance"] is False
    assert above_response["overall"]["percentage"] == 100.0
    assert below_response["threshold"] == 75.0


def test_student_dashboard_pending_correction_count(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "pend@example.com", "P1")
    session = _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], status="ABSENT", date_str="2025-08-01",
    )
    record = client.get(f"/api/v1/attendance-sessions/{session['id']}/records", headers=admin_headers).json()[0]
    student_headers = _login_headers(client, student["email"], "student-password-123")
    client.post(
        f"/api/v1/attendance-records/{record['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "Reason."}, headers=student_headers,
    )

    response = client.get("/api/v1/dashboard/student", headers=student_headers)

    assert response.json()["pending_correction_requests"] == 1
