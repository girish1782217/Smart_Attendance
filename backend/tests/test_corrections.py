from app.core.roles import RoleName
from app.models.audit_log import AuditAction, AuditLog


def _setup_submitted_session(client, admin_headers, num_students=2):
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
    client.put(
        f"/api/v1/attendance-sessions/{session['id']}/records",
        json={"records": [{"student_id": s["id"], "status": "ABSENT"} for s in students]},
        headers=admin_headers,
    )
    client.post(f"/api/v1/attendance-sessions/{session['id']}/submit", headers=admin_headers)
    records = client.get(
        f"/api/v1/attendance-sessions/{session['id']}/records", headers=admin_headers
    ).json()
    records_by_student = {r["student_id"]: r for r in records}
    return {
        "faculty": faculty,
        "students": students,
        "session": session,
        "records": records_by_student,
    }


def _login_headers(client, email, password):
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_student_requests_correction_on_own_record(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_submitted_session(client, admin_headers)
    student = ctx["students"][0]
    record = ctx["records"][student["id"]]
    student_headers = _login_headers(client, student["email"], "student-password-123")

    response = client.post(
        f"/api/v1/attendance-records/{record['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "I was marked absent by mistake."},
        headers=student_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["original_status"] == "ABSENT"
    assert body["requested_status"] == "PRESENT"


def test_student_cannot_request_correction_on_another_students_record(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_submitted_session(client, admin_headers)
    other_record = ctx["records"][ctx["students"][1]["id"]]
    student_headers = _login_headers(client, ctx["students"][0]["email"], "student-password-123")

    response = client.post(
        f"/api/v1/attendance-records/{other_record['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "Not mine but trying anyway."},
        headers=student_headers,
    )

    assert response.status_code == 403


def test_correction_on_non_submitted_session_returns_409(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_submitted_session(client, admin_headers)
    # Create a second, still-SCHEDULED session/record to test against.
    first_session = client.get(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}", headers=admin_headers
    ).json()
    session2 = client.post(
        "/api/v1/attendance-sessions",
        json={
            "faculty_id": ctx["faculty"]["id"],
            "subject_id": first_session["subject_id"],
            "section_id": first_session["section_id"],
            "session_date": "2025-08-02",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
        },
        headers=admin_headers,
    ).json()
    client.put(
        f"/api/v1/attendance-sessions/{session2['id']}/records",
        json={"records": [{"student_id": ctx["students"][0]["id"], "status": "ABSENT"}]},
        headers=admin_headers,
    )
    unsubmitted_record = client.get(
        f"/api/v1/attendance-sessions/{session2['id']}/records", headers=admin_headers
    ).json()[0]

    response = client.post(
        f"/api/v1/attendance-records/{unsubmitted_record['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "Too early."},
        headers=admin_headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_NOT_SUBMITTED"


def test_duplicate_pending_correction_returns_409(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_submitted_session(client, admin_headers)
    student = ctx["students"][0]
    record = ctx["records"][student["id"]]
    student_headers = _login_headers(client, student["email"], "student-password-123")
    client.post(
        f"/api/v1/attendance-records/{record['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "First request."},
        headers=student_headers,
    )

    response = client.post(
        f"/api/v1/attendance-records/{record['id']}/corrections",
        json={"requested_status": "LATE", "reason": "Second request."},
        headers=student_headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CORRECTION_ALREADY_PENDING"


def test_admin_approves_correction_updates_record_and_preserves_history(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_submitted_session(client, admin_headers)
    student = ctx["students"][0]
    record = ctx["records"][student["id"]]
    student_headers = _login_headers(client, student["email"], "student-password-123")
    created = client.post(
        f"/api/v1/attendance-records/{record['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "I was actually present."},
        headers=student_headers,
    ).json()

    response = client.post(
        f"/api/v1/corrections/{created['id']}/approve",
        json={"decision_reason": "Verified with sign-in sheet."},
        headers=admin_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "APPROVED"
    assert body["original_status"] == "ABSENT"  # history preserved
    assert body["requested_status"] == "PRESENT"

    updated_records = client.get(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/records", headers=admin_headers
    ).json()
    updated = next(r for r in updated_records if r["student_id"] == student["id"])
    assert updated["status"] == "PRESENT"


def test_faculty_cannot_self_review_own_request(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_submitted_session(client, admin_headers)
    student = ctx["students"][0]
    record = ctx["records"][student["id"]]
    faculty_headers = _login_headers(client, ctx["faculty"]["email"], "faculty-password-123")
    created = client.post(
        f"/api/v1/attendance-records/{record['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "Faculty noticed an error."},
        headers=faculty_headers,
    ).json()

    response = client.post(
        f"/api/v1/corrections/{created['id']}/approve", json={}, headers=faculty_headers
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SELF_REVIEW_NOT_ALLOWED"

    # But admin can still decide it.
    admin_response = client.post(
        f"/api/v1/corrections/{created['id']}/approve", json={}, headers=admin_headers
    )
    assert admin_response.status_code == 200


def test_approving_already_decided_correction_returns_409(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_submitted_session(client, admin_headers)
    student = ctx["students"][0]
    record = ctx["records"][student["id"]]
    student_headers = _login_headers(client, student["email"], "student-password-123")
    created = client.post(
        f"/api/v1/attendance-records/{record['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "Reason."},
        headers=student_headers,
    ).json()
    client.post(f"/api/v1/corrections/{created['id']}/approve", json={}, headers=admin_headers)

    response = client.post(
        f"/api/v1/corrections/{created['id']}/approve", json={}, headers=admin_headers
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CORRECTION_ALREADY_DECIDED"


def test_reject_leaves_record_unchanged(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_submitted_session(client, admin_headers)
    student = ctx["students"][0]
    record = ctx["records"][student["id"]]
    student_headers = _login_headers(client, student["email"], "student-password-123")
    created = client.post(
        f"/api/v1/attendance-records/{record['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "Reason."},
        headers=student_headers,
    ).json()

    response = client.post(
        f"/api/v1/corrections/{created['id']}/reject",
        json={"decision_reason": "No evidence provided."},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"

    records = client.get(
        f"/api/v1/attendance-sessions/{ctx['session']['id']}/records", headers=admin_headers
    ).json()
    unchanged = next(r for r in records if r["student_id"] == student["id"])
    assert unchanged["status"] == "ABSENT"


def test_approve_and_reject_each_write_exactly_one_audit_log_row(client, make_auth_headers, db_session):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_submitted_session(client, admin_headers, num_students=2)
    student0, student1 = ctx["students"]
    record0 = ctx["records"][student0["id"]]
    record1 = ctx["records"][student1["id"]]
    headers0 = _login_headers(client, student0["email"], "student-password-123")
    headers1 = _login_headers(client, student1["email"], "student-password-123")

    correction0 = client.post(
        f"/api/v1/attendance-records/{record0['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "Approve me."},
        headers=headers0,
    ).json()
    correction1 = client.post(
        f"/api/v1/attendance-records/{record1['id']}/corrections",
        json={"requested_status": "LATE", "reason": "Reject me."},
        headers=headers1,
    ).json()

    requested_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.CORRECTION_REQUESTED.value
    ).all()
    assert len(requested_logs) == 2

    client.post(
        f"/api/v1/corrections/{correction0['id']}/approve",
        json={"decision_reason": "Confirmed."},
        headers=admin_headers,
    )
    client.post(
        f"/api/v1/corrections/{correction1['id']}/reject",
        json={"decision_reason": "No evidence."},
        headers=admin_headers,
    )

    approved_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.CORRECTION_APPROVED.value
    ).all()
    rejected_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.CORRECTION_REJECTED.value
    ).all()

    assert len(approved_logs) == 1
    assert approved_logs[0].entity_id == record0["id"]
    assert approved_logs[0].before_value == "ABSENT"
    assert approved_logs[0].after_value == "PRESENT"
    assert approved_logs[0].reason == "Confirmed."

    assert len(rejected_logs) == 1
    assert rejected_logs[0].entity_id == record1["id"]
    assert rejected_logs[0].before_value == "ABSENT"
    assert rejected_logs[0].after_value == "ABSENT"  # rejection: record unchanged
    assert rejected_logs[0].reason == "No evidence."


def test_student_sees_only_corrections_about_their_own_records(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup_submitted_session(client, admin_headers)
    record0 = ctx["records"][ctx["students"][0]["id"]]
    record1 = ctx["records"][ctx["students"][1]["id"]]
    headers0 = _login_headers(client, ctx["students"][0]["email"], "student-password-123")
    headers1 = _login_headers(client, ctx["students"][1]["email"], "student-password-123")
    client.post(
        f"/api/v1/attendance-records/{record0['id']}/corrections",
        json={"requested_status": "PRESENT", "reason": "Reason 0."},
        headers=headers0,
    )
    client.post(
        f"/api/v1/attendance-records/{record1['id']}/corrections",
        json={"requested_status": "LATE", "reason": "Reason 1."},
        headers=headers1,
    )

    response = client.get("/api/v1/corrections", headers=headers0)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["student_id"] == ctx["students"][0]["id"]
