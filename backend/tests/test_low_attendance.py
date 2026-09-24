from app.core.roles import RoleName


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


def _mark_records(
    client, admin_headers, *, faculty_id, subject_id, section_id, student_id, statuses, date_offset=0
):
    """Creates one submitted session per status, each marking only this
    student. `date_offset` must be varied across calls sharing the same
    section, so sessions don't collide with SPEC 07's overlap-prevention
    rule (same section+date+time is rejected regardless of subject)."""
    for i, status in enumerate(statuses):
        session = client.post(
            "/api/v1/attendance-sessions",
            json={
                "faculty_id": faculty_id,
                "subject_id": subject_id,
                "section_id": section_id,
                "session_date": f"2025-08-{date_offset + i + 1:02d}",
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


def test_admin_can_read_and_update_threshold(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])

    default_response = client.get("/api/v1/settings/low-attendance-threshold", headers=admin_headers)
    assert default_response.status_code == 200
    assert default_response.json()["threshold"] == 75.0

    update_response = client.put(
        "/api/v1/settings/low-attendance-threshold", json={"threshold": 80.0}, headers=admin_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["threshold"] == 80.0

    read_after_update = client.get("/api/v1/settings/low-attendance-threshold", headers=admin_headers)
    assert read_after_update.json()["threshold"] == 80.0


def test_faculty_cannot_update_threshold(client, make_auth_headers):
    faculty_headers = make_auth_headers([RoleName.FACULTY])

    response = client.put(
        "/api/v1/settings/low-attendance-threshold", json={"threshold": 90.0}, headers=faculty_headers
    )

    assert response.status_code == 403


def test_student_exactly_at_threshold_is_excluded(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    # 3 present out of 4 -> exactly 75.0%, the default threshold.
    student = _create_student(client, admin_headers, ctx["section"]["id"], "s1@example.com", "R1")
    _mark_records(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"],
        statuses=["PRESENT", "PRESENT", "PRESENT", "ABSENT"],
    )

    response = client.get("/api/v1/reports/low-attendance/overall", headers=admin_headers)

    assert response.status_code == 200
    student_ids = {row["student_id"] for row in response.json()["items"]}
    assert student["id"] not in student_ids


def test_student_below_threshold_is_included_above_is_not(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    below = _create_student(client, admin_headers, ctx["section"]["id"], "below@example.com", "R2")
    above = _create_student(client, admin_headers, ctx["section"]["id"], "above@example.com", "R3")
    # below: 2/4 = 50% (< 75%)
    _mark_records(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=below["id"],
        statuses=["PRESENT", "ABSENT", "PRESENT", "ABSENT"], date_offset=0,
    )
    # above: 4/4 = 100% (> 75%) -- same section, so needs non-overlapping dates.
    _mark_records(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=above["id"],
        statuses=["PRESENT", "PRESENT", "PRESENT", "PRESENT"], date_offset=4,
    )

    response = client.get("/api/v1/reports/low-attendance/overall", headers=admin_headers)

    body = response.json()
    student_ids = {row["student_id"] for row in body["items"]}
    assert below["id"] in student_ids
    assert above["id"] not in student_ids
    below_row = next(row for row in body["items"] if row["student_id"] == below["id"])
    assert below_row["percentage"] == 50.0


def test_student_with_no_attendance_data_never_appears(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "noattend@example.com", "R4")

    response = client.get("/api/v1/reports/low-attendance/overall", headers=admin_headers)

    student_ids = {row["student_id"] for row in response.json()["items"]}
    assert student["id"] not in student_ids


def test_multiple_subjects_appear_separately_in_by_subject_report(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    subject2 = client.post(
        "/api/v1/subjects",
        json={"name": "Algorithms", "code": "CS-ALGO", "department_id": ctx["department"]["id"]},
        headers=admin_headers,
    ).json()
    year_resp = client.get("/api/v1/academic-years", headers=admin_headers).json()["items"][0]
    semester_resp = client.get("/api/v1/semesters", headers=admin_headers).json()["items"][0]
    client.post(
        "/api/v1/faculty-assignments",
        json={
            "faculty_id": ctx["faculty"]["id"],
            "subject_id": subject2["id"],
            "section_id": ctx["section"]["id"],
            "semester_id": semester_resp["id"],
        },
        headers=admin_headers,
    )
    student = _create_student(client, admin_headers, ctx["section"]["id"], "multi@example.com", "R5")
    # Both subjects below threshold. Same section -> non-overlapping dates.
    _mark_records(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], statuses=["ABSENT", "ABSENT"],
        date_offset=0,
    )
    _mark_records(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=subject2["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], statuses=["ABSENT", "ABSENT"],
        date_offset=2,
    )

    response = client.get("/api/v1/reports/low-attendance/by-subject", headers=admin_headers)

    rows = [row for row in response.json()["items"] if row["student_id"] == student["id"]]
    subject_codes = {row["subject_code"] for row in rows}
    assert len(rows) == 2
    assert subject_codes == {ctx["subject"]["code"], "CS-ALGO"}

    # And the overall report aggregates the same student into a single row.
    overall_response = client.get("/api/v1/reports/low-attendance/overall", headers=admin_headers)
    overall_rows = [
        row for row in overall_response.json()["items"] if row["student_id"] == student["id"]
    ]
    assert len(overall_rows) == 1
    assert overall_rows[0]["percentage"] == 0.0


def test_department_filter_narrows_results(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx_cse = _setup(client, admin_headers, "Computer Science", "CSE")
    ctx_ece = _setup(client, admin_headers, "Electronics", "ECE")
    student_cse = _create_student(client, admin_headers, ctx_cse["section"]["id"], "cse@example.com", "CSE1")
    student_ece = _create_student(client, admin_headers, ctx_ece["section"]["id"], "ece@example.com", "ECE1")
    for ctx, student in [(ctx_cse, student_cse), (ctx_ece, student_ece)]:
        _mark_records(
            client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
            section_id=ctx["section"]["id"], student_id=student["id"], statuses=["ABSENT", "ABSENT"],
        )

    response = client.get(
        f"/api/v1/reports/low-attendance/overall?department_id={ctx_cse['department']['id']}",
        headers=admin_headers,
    )

    student_ids = {row["student_id"] for row in response.json()["items"]}
    assert student_cse["id"] in student_ids
    assert student_ece["id"] not in student_ids


def test_per_request_threshold_override_does_not_persist(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "override@example.com", "R6")
    # 3/4 = 75% -- excluded at default threshold (75), included if threshold override is 80.
    _mark_records(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"],
        statuses=["PRESENT", "PRESENT", "PRESENT", "ABSENT"],
    )

    with_override = client.get(
        "/api/v1/reports/low-attendance/overall?threshold=80", headers=admin_headers
    ).json()
    assert student["id"] in {row["student_id"] for row in with_override["items"]}
    assert with_override["threshold"] == 80.0

    without_override = client.get("/api/v1/reports/low-attendance/overall", headers=admin_headers).json()
    assert student["id"] not in {row["student_id"] for row in without_override["items"]}
    assert without_override["threshold"] == 75.0


def test_student_role_forbidden_on_reports(client, make_auth_headers):
    student_headers = make_auth_headers([RoleName.STUDENT])

    response = client.get("/api/v1/reports/low-attendance/overall", headers=student_headers)

    assert response.status_code == 403
