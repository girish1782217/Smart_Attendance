from app.core.roles import RoleName


def _create_department(client, headers, name="Computer Science", code="CSE"):
    return client.post("/api/v1/departments", json={"name": name, "code": code}, headers=headers).json()


def _faculty_payload(department_id, email="faculty1@example.com", employee_id="EMP001"):
    return {
        "email": email,
        "full_name": "Dr. Jane Faculty",
        "password": "faculty-password-123",
        "employee_id": employee_id,
        "department_id": department_id,
        "phone": "9999999999",
    }


def test_admin_can_create_faculty_with_backing_user(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    dept = _create_department(client, headers)

    response = client.post("/api/v1/faculty", json=_faculty_payload(dept["id"]), headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "faculty1@example.com"
    assert body["employee_id"] == "EMP001"

    login = client.post(
        "/api/v1/auth/login", json={"email": "faculty1@example.com", "password": "faculty-password-123"}
    )
    assert login.status_code == 200


def test_duplicate_employee_id_returns_conflict(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    dept = _create_department(client, headers)
    client.post("/api/v1/faculty", json=_faculty_payload(dept["id"]), headers=headers)

    response = client.post(
        "/api/v1/faculty",
        json=_faculty_payload(dept["id"], email="other@example.com", employee_id="EMP001"),
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "FACULTY_EMPLOYEE_ID_DUPLICATE"


def test_create_faculty_with_missing_department_returns_404(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])

    response = client.post("/api/v1/faculty", json=_faculty_payload(999), headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DEPARTMENT_NOT_FOUND"


def test_student_cannot_access_faculty_endpoints(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    dept = _create_department(client, admin_headers)
    client.post("/api/v1/faculty", json=_faculty_payload(dept["id"]), headers=admin_headers)

    student_headers = make_auth_headers([RoleName.STUDENT])
    response = client.get("/api/v1/faculty", headers=student_headers)
    assert response.status_code == 403


def test_faculty_can_list_and_get_but_not_mutate(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    dept = _create_department(client, admin_headers)
    created = client.post(
        "/api/v1/faculty", json=_faculty_payload(dept["id"]), headers=admin_headers
    ).json()

    faculty_headers = make_auth_headers([RoleName.FACULTY])
    list_response = client.get("/api/v1/faculty", headers=faculty_headers)
    assert list_response.status_code == 200

    get_response = client.get(f"/api/v1/faculty/{created['id']}", headers=faculty_headers)
    assert get_response.status_code == 200

    patch_response = client.patch(
        f"/api/v1/faculty/{created['id']}", json={"phone": "1111111111"}, headers=faculty_headers
    )
    assert patch_response.status_code == 403


def test_deactivate_faculty_disables_login(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    dept = _create_department(client, headers)
    created = client.post("/api/v1/faculty", json=_faculty_payload(dept["id"]), headers=headers).json()

    response = client.delete(f"/api/v1/faculty/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    login = client.post(
        "/api/v1/auth/login", json={"email": "faculty1@example.com", "password": "faculty-password-123"}
    )
    assert login.status_code == 401


# ---------------------------------------------------------------------------
# FacultyAssignment
# ---------------------------------------------------------------------------


def _full_hierarchy(client, headers):
    dept = _create_department(client, headers)
    program = client.post(
        "/api/v1/programs",
        json={"name": "B.Tech CSE", "code": "BTCSE", "department_id": dept["id"]},
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
        json={"name": "Data Structures", "code": "CS201", "department_id": dept["id"]},
        headers=headers,
    ).json()
    year = client.post(
        "/api/v1/academic-years",
        json={"name": "2025-2026", "start_date": "2025-06-01", "end_date": "2026-05-31"},
        headers=headers,
    ).json()
    semester = client.post(
        "/api/v1/semesters",
        json={
            "name": "Semester 1",
            "academic_year_id": year["id"],
            "start_date": "2025-06-01",
            "end_date": "2025-11-30",
        },
        headers=headers,
    ).json()
    faculty = client.post("/api/v1/faculty", json=_faculty_payload(dept["id"]), headers=headers).json()
    return {"section": section, "subject": subject, "semester": semester, "faculty": faculty}


def test_create_assignment_success(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    ctx = _full_hierarchy(client, headers)

    response = client.post(
        "/api/v1/faculty-assignments",
        json={
            "faculty_id": ctx["faculty"]["id"],
            "subject_id": ctx["subject"]["id"],
            "section_id": ctx["section"]["id"],
            "semester_id": ctx["semester"]["id"],
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["is_active"] is True


def test_create_assignment_with_missing_faculty_returns_404(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    ctx = _full_hierarchy(client, headers)

    response = client.post(
        "/api/v1/faculty-assignments",
        json={
            "faculty_id": 999,
            "subject_id": ctx["subject"]["id"],
            "section_id": ctx["section"]["id"],
            "semester_id": ctx["semester"]["id"],
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FACULTY_NOT_FOUND"


def test_duplicate_assignment_returns_conflict(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    ctx = _full_hierarchy(client, headers)
    payload = {
        "faculty_id": ctx["faculty"]["id"],
        "subject_id": ctx["subject"]["id"],
        "section_id": ctx["section"]["id"],
        "semester_id": ctx["semester"]["id"],
    }
    client.post("/api/v1/faculty-assignments", json=payload, headers=headers)

    response = client.post("/api/v1/faculty-assignments", json=payload, headers=headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ASSIGNMENT_DUPLICATE"


def test_faculty_sees_only_own_assignments_regardless_of_query_param(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    ctx = _full_hierarchy(client, admin_headers)
    client.post(
        "/api/v1/faculty-assignments",
        json={
            "faculty_id": ctx["faculty"]["id"],
            "subject_id": ctx["subject"]["id"],
            "section_id": ctx["section"]["id"],
            "semester_id": ctx["semester"]["id"],
        },
        headers=admin_headers,
    )

    # A second, unrelated faculty member (with a real Faculty profile, just
    # no assignments of their own) created via the real endpoint.
    dept = _create_department(client, admin_headers, "Electronics", "ECE")
    client.post(
        "/api/v1/faculty",
        json=_faculty_payload(dept["id"], email="other-faculty@example.com", employee_id="EMP999"),
        headers=admin_headers,
    )
    other_login = client.post(
        "/api/v1/auth/login",
        json={"email": "other-faculty@example.com", "password": "faculty-password-123"},
    )
    other_faculty_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    # Even explicitly requesting the first faculty's id, the caller only
    # ever sees their own (empty) list — the server ignores the param.
    response = client.get(
        f"/api/v1/faculty-assignments?faculty_id={ctx['faculty']['id']}", headers=other_faculty_headers
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_faculty_role_with_no_linked_profile_gets_404_on_assignments(client, make_auth_headers):
    """A FACULTY-role user provisioned generically (e.g. via POST
    /api/v1/users, bypassing the faculty_service create flow) has no linked
    Faculty row — a documented edge case, not a bug."""
    headers = make_auth_headers([RoleName.FACULTY])

    response = client.get("/api/v1/faculty-assignments", headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FACULTY_PROFILE_NOT_FOUND"


def test_admin_can_deactivate_assignment(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    ctx = _full_hierarchy(client, headers)
    created = client.post(
        "/api/v1/faculty-assignments",
        json={
            "faculty_id": ctx["faculty"]["id"],
            "subject_id": ctx["subject"]["id"],
            "section_id": ctx["section"]["id"],
            "semester_id": ctx["semester"]["id"],
        },
        headers=headers,
    ).json()

    response = client.delete(f"/api/v1/faculty-assignments/{created['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Deactivating clears the way to create the same assignment again
    # (get_active_duplicate only matches is_active=True rows).
    recreated = client.post(
        "/api/v1/faculty-assignments",
        json={
            "faculty_id": ctx["faculty"]["id"],
            "subject_id": ctx["subject"]["id"],
            "section_id": ctx["section"]["id"],
            "semester_id": ctx["semester"]["id"],
        },
        headers=headers,
    )
    assert recreated.status_code == 201
