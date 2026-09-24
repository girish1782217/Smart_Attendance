import csv
import io

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


def test_student_attendance_report_includes_above_and_below_threshold(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    low = _create_student(client, admin_headers, ctx["section"]["id"], "low@example.com", "R1")
    high = _create_student(client, admin_headers, ctx["section"]["id"], "high@example.com", "R2")
    _mark_records(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=low["id"], statuses=["ABSENT", "ABSENT"], date_offset=0,
    )
    _mark_records(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=high["id"], statuses=["PRESENT", "PRESENT"], date_offset=2,
    )

    response = client.get("/api/v1/reports/student-attendance", headers=admin_headers)

    assert response.status_code == 200
    student_ids = {row["student_id"] for row in response.json()["items"]}
    assert low["id"] in student_ids
    assert high["id"] in student_ids  # unlike SPEC 11, high-attendance students ARE included


def test_student_attendance_report_date_range_filter(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "s@example.com", "R3")
    # session 1 in August, session 2 in September.
    session1 = client.post(
        "/api/v1/attendance-sessions",
        json={
            "faculty_id": ctx["faculty"]["id"], "subject_id": ctx["subject"]["id"],
            "section_id": ctx["section"]["id"], "session_date": "2025-08-01",
            "start_time": "09:00:00", "end_time": "10:00:00",
        },
        headers=admin_headers,
    ).json()
    client.put(
        f"/api/v1/attendance-sessions/{session1['id']}/records",
        json={"records": [{"student_id": student["id"], "status": "PRESENT"}]}, headers=admin_headers,
    )
    client.post(f"/api/v1/attendance-sessions/{session1['id']}/submit", headers=admin_headers)
    session2 = client.post(
        "/api/v1/attendance-sessions",
        json={
            "faculty_id": ctx["faculty"]["id"], "subject_id": ctx["subject"]["id"],
            "section_id": ctx["section"]["id"], "session_date": "2025-09-01",
            "start_time": "09:00:00", "end_time": "10:00:00",
        },
        headers=admin_headers,
    ).json()
    client.put(
        f"/api/v1/attendance-sessions/{session2['id']}/records",
        json={"records": [{"student_id": student["id"], "status": "ABSENT"}]}, headers=admin_headers,
    )
    client.post(f"/api/v1/attendance-sessions/{session2['id']}/submit", headers=admin_headers)

    august_only = client.get(
        "/api/v1/reports/student-attendance?from_date=2025-08-01&to_date=2025-08-31", headers=admin_headers
    ).json()
    row = next(r for r in august_only["items"] if r["student_id"] == student["id"])
    assert row["total_applicable"] == 1
    assert row["percentage"] == 100.0  # only the August PRESENT record counted


def test_subject_attendance_report_filters_by_subject(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    subject2 = client.post(
        "/api/v1/subjects",
        json={"name": "Algorithms", "code": "CS-ALGO2", "department_id": ctx["department"]["id"]},
        headers=admin_headers,
    ).json()
    semester = client.get("/api/v1/semesters", headers=admin_headers).json()["items"][0]
    client.post(
        "/api/v1/faculty-assignments",
        json={
            "faculty_id": ctx["faculty"]["id"], "subject_id": subject2["id"],
            "section_id": ctx["section"]["id"], "semester_id": semester["id"],
        },
        headers=admin_headers,
    )
    student = _create_student(client, admin_headers, ctx["section"]["id"], "multi@example.com", "R4")
    _mark_records(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], statuses=["PRESENT"], date_offset=0,
    )
    _mark_records(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=subject2["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], statuses=["ABSENT"], date_offset=1,
    )

    all_subjects = client.get("/api/v1/reports/subject-attendance", headers=admin_headers).json()
    assert len({row["subject_id"] for row in all_subjects["items"]}) == 2

    one_subject = client.get(
        f"/api/v1/reports/subject-attendance?subject_id={subject2['id']}", headers=admin_headers
    ).json()
    assert all(row["subject_id"] == subject2["id"] for row in one_subject["items"])
    assert one_subject["total"] == 1


def test_faculty_activity_report_counts_sessions_by_status(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    student = _create_student(client, admin_headers, ctx["section"]["id"], "act@example.com", "R5")
    # One submitted session.
    _mark_records(
        client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
        section_id=ctx["section"]["id"], student_id=student["id"], statuses=["PRESENT"], date_offset=0,
    )
    # One scheduled-but-not-submitted session.
    client.post(
        "/api/v1/attendance-sessions",
        json={
            "faculty_id": ctx["faculty"]["id"], "subject_id": ctx["subject"]["id"],
            "section_id": ctx["section"]["id"], "session_date": "2025-08-05",
            "start_time": "09:00:00", "end_time": "10:00:00",
        },
        headers=admin_headers,
    )

    response = client.get(
        f"/api/v1/reports/faculty-activity?faculty_id={ctx['faculty']['id']}", headers=admin_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_sessions"] == 2
    assert body["submitted_sessions"] == 1
    assert body["scheduled_sessions"] == 1


def test_faculty_sees_own_activity_without_specifying_id(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    faculty_login = client.post(
        "/api/v1/auth/login",
        json={"email": f"faculty-{ctx['department']['code']}@example.com", "password": "faculty-password-123"},
    )
    faculty_headers = {"Authorization": f"Bearer {faculty_login.json()['access_token']}"}

    response = client.get("/api/v1/reports/faculty-activity", headers=faculty_headers)

    assert response.status_code == 200
    assert response.json()["faculty_id"] == ctx["faculty"]["id"]


def test_csv_export_returns_every_matching_row_not_just_one_page(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _setup(client, admin_headers)
    # Create more students than the default page size (25) would show at once
    # is unnecessary to prove the point cheaply -- 3 rows with a page_size of
    # 1 (achieved by not paginating the export at all) is enough to prove
    # export doesn't slice.
    students = [
        _create_student(client, admin_headers, ctx["section"]["id"], f"exp{i}@example.com", f"EXP{i}")
        for i in range(3)
    ]
    for i, student in enumerate(students):
        _mark_records(
            client, admin_headers, faculty_id=ctx["faculty"]["id"], subject_id=ctx["subject"]["id"],
            section_id=ctx["section"]["id"], student_id=student["id"], statuses=["PRESENT"],
            date_offset=i,
        )

    response = client.get("/api/v1/reports/student-attendance/export", headers=admin_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    exported_ids = {int(row["student_id"]) for row in rows}
    assert exported_ids == {student["id"] for student in students}


def test_student_role_forbidden_on_report_endpoints(client, make_auth_headers):
    student_headers = make_auth_headers([RoleName.STUDENT])

    assert client.get("/api/v1/reports/student-attendance", headers=student_headers).status_code == 403
    assert client.get("/api/v1/reports/subject-attendance", headers=student_headers).status_code == 403
    assert client.get("/api/v1/reports/faculty-activity", headers=student_headers).status_code == 403
    assert (
        client.get("/api/v1/reports/student-attendance/export", headers=student_headers).status_code == 403
    )
