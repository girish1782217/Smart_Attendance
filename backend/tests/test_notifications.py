from app.core.roles import RoleName


def _login_headers(client, email, password):
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _setup(client, admin_headers, num_students=1):
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
    students = [
        client.post(
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
        for i in range(num_students)
    ]
    return {"section": section, "subject": subject, "faculty": faculty, "students": students}


def _mark_and_submit(
    client,
    admin_headers,
    *,
    faculty_id,
    subject_id,
    section_id,
    student_id,
    status,
    date_str,
    other_student_ids=(),
):
    """Marks `student_id` with `status` and any `other_student_ids` as
    PRESENT (SPEC 08's submit requires the *entire* section roster to be
    marked, not just the student under test)."""
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
        f"/api/v1/attendance-sessions/{session['id']}/records",
        json={"records": records},
        headers=admin_headers,
    )
    client.post(f"/api/v1/attendance-sessions/{session['id']}/submit", headers=admin_headers)
    return session


def test_correction_requested_notifies_owning_faculty(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = ctx["students"][0]
    session = _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], status="ABSENT", date_str="2025-08-01",
    )
    record = client.get(f"/api/v1/attendance-sessions/{session['id']}/records", headers=admin_headers).json()[0]
    student_headers = _login_headers(client, student["email"], "student-password-123")
    client.post(
        f"/api/v1/attendance-records/{record['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "Mistake."},
        headers=student_headers,
    )

    faculty_headers = _login_headers(client, ctx["faculty"]["email"], "faculty-password-123")
    response = client.get("/api/v1/notifications", headers=faculty_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "CORRECTION_REQUESTED"
    assert body["items"][0]["is_read"] is False


def test_faculty_self_correction_does_not_self_notify(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = ctx["students"][0]
    session = _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], status="ABSENT", date_str="2025-08-01",
    )
    record = client.get(f"/api/v1/attendance-sessions/{session['id']}/records", headers=admin_headers).json()[0]
    faculty_headers = _login_headers(client, ctx["faculty"]["email"], "faculty-password-123")
    client.post(
        f"/api/v1/attendance-records/{record['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "I noticed an error."},
        headers=faculty_headers,
    )

    response = client.get("/api/v1/notifications", headers=faculty_headers)

    assert response.json()["total"] == 0


def test_approval_and_rejection_notify_requester(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=2)
    student0, student1 = ctx["students"]
    session0 = _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student0["id"], status="ABSENT", date_str="2025-08-01",
        other_student_ids=[student1["id"]],
    )
    session1 = _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student1["id"], status="ABSENT", date_str="2025-08-02",
        other_student_ids=[student0["id"]],
    )
    record0 = next(
        r for r in client.get(f"/api/v1/attendance-sessions/{session0['id']}/records", headers=admin_headers).json()
        if r["student_id"] == student0["id"]
    )
    record1 = next(
        r for r in client.get(f"/api/v1/attendance-sessions/{session1['id']}/records", headers=admin_headers).json()
        if r["student_id"] == student1["id"]
    )
    headers0 = _login_headers(client, student0["email"], "student-password-123")
    headers1 = _login_headers(client, student1["email"], "student-password-123")
    correction0 = client.post(
        f"/api/v1/attendance-records/{record0['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "Approve me."}, headers=headers0,
    ).json()
    correction1 = client.post(
        f"/api/v1/attendance-records/{record1['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "Reject me."}, headers=headers1,
    ).json()

    client.post(f"/api/v1/corrections/{correction0['id']}/approve", json={}, headers=admin_headers)
    client.post(f"/api/v1/corrections/{correction1['id']}/reject", json={}, headers=admin_headers)

    notifications0 = client.get("/api/v1/notifications", headers=headers0).json()["items"]
    notifications1 = client.get("/api/v1/notifications", headers=headers1).json()["items"]

    assert any(n["type"] == "CORRECTION_APPROVED" for n in notifications0)
    assert any(n["type"] == "CORRECTION_REJECTED" for n in notifications1)


def test_notifications_are_strictly_per_user(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=2)
    student0, student1 = ctx["students"]
    session0 = _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student0["id"], status="ABSENT", date_str="2025-08-01",
        other_student_ids=[student1["id"]],
    )
    record0 = next(
        r for r in client.get(f"/api/v1/attendance-sessions/{session0['id']}/records", headers=admin_headers).json()
        if r["student_id"] == student0["id"]
    )
    headers0 = _login_headers(client, student0["email"], "student-password-123")
    headers1 = _login_headers(client, student1["email"], "student-password-123")
    correction0 = client.post(
        f"/api/v1/attendance-records/{record0['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "Reason."}, headers=headers0,
    ).json()
    client.post(f"/api/v1/corrections/{correction0['id']}/approve", json={}, headers=admin_headers)

    response1 = client.get("/api/v1/notifications", headers=headers1)

    assert response1.json()["total"] == 0


def test_mark_read_updates_state_and_rejects_other_users_notification(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=2)
    student0, student1 = ctx["students"]
    # PRESENT (not ABSENT) deliberately, so this test isn't confounded by
    # SPEC 13's low-attendance-warning side effect on submit.
    session0 = _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student0["id"], status="PRESENT", date_str="2025-08-01",
        other_student_ids=[student1["id"]],
    )
    record0 = next(
        r for r in client.get(f"/api/v1/attendance-sessions/{session0['id']}/records", headers=admin_headers).json()
        if r["student_id"] == student0["id"]
    )
    headers0 = _login_headers(client, student0["email"], "student-password-123")
    headers1 = _login_headers(client, student1["email"], "student-password-123")
    correction0 = client.post(
        f"/api/v1/attendance-records/{record0['id']}/corrections",
        json={"requested_status": "LATE", "reason": "Reason."}, headers=headers0,
    ).json()
    client.post(f"/api/v1/corrections/{correction0['id']}/approve", json={}, headers=admin_headers)
    notification = client.get("/api/v1/notifications", headers=headers0).json()["items"][0]

    other_user_attempt = client.post(
        f"/api/v1/notifications/{notification['id']}/read", headers=headers1
    )
    assert other_user_attempt.status_code == 404

    own_attempt = client.post(f"/api/v1/notifications/{notification['id']}/read", headers=headers0)
    assert own_attempt.status_code == 200
    assert own_attempt.json()["is_read"] is True
    assert own_attempt.json()["read_at"] is not None

    unread_count = client.get("/api/v1/notifications/unread-count", headers=headers0).json()
    assert unread_count["count"] == 0


def test_low_attendance_warning_created_once_and_deduplicated(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=1)
    student = ctx["students"][0]
    student_headers = _login_headers(client, student["email"], "student-password-123")

    # First ABSENT session pushes them to 0% -- below the 75% default threshold.
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], status="ABSENT", date_str="2025-08-01",
    )
    first_check = client.get("/api/v1/notifications", headers=student_headers).json()
    assert first_check["total"] == 1
    assert first_check["items"][0]["type"] == "LOW_ATTENDANCE_WARNING"

    # A second ABSENT session -- still below threshold, but the first
    # warning is still unread, so no duplicate should be created.
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], status="ABSENT", date_str="2025-08-02",
    )
    second_check = client.get("/api/v1/notifications", headers=student_headers).json()
    assert second_check["total"] == 1  # still just one, not two

    # After marking it read, a further drop creates a new one.
    client.post(f"/api/v1/notifications/{first_check['items'][0]['id']}/read", headers=student_headers)
    _mark_and_submit(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], status="ABSENT", date_str="2025-08-03",
    )
    third_check = client.get("/api/v1/notifications", headers=student_headers).json()
    assert third_check["total"] == 2


def test_student_role_cannot_notify_others_via_side_effects_but_can_view_own(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers, num_students=1)
    student_headers = _login_headers(client, ctx["students"][0]["email"], "student-password-123")

    response = client.get("/api/v1/notifications", headers=student_headers)

    assert response.status_code == 200
    assert response.json()["total"] == 0
