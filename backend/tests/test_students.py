from app.core.roles import RoleName


def _create_department(client, headers, name="Computer Science", code="CSE"):
    return client.post("/api/v1/departments", json={"name": name, "code": code}, headers=headers).json()


def _create_section(client, headers, dept_name="Computer Science", dept_code="CSE"):
    dept = _create_department(client, headers, dept_name, dept_code)
    program = client.post(
        "/api/v1/programs",
        json={"name": "B.Tech CSE", "code": f"BT{dept_code}", "department_id": dept["id"]},
        headers=headers,
    ).json()
    academic_class = client.post(
        "/api/v1/classes", json={"name": "First Year", "program_id": program["id"]}, headers=headers
    ).json()
    return client.post(
        "/api/v1/sections",
        json={"name": "A", "class_id": academic_class["id"], "capacity": 60},
        headers=headers,
    ).json()


def _student_payload(section_id, email="student1@example.com", roll_number="CSE2025001"):
    return {
        "email": email,
        "full_name": "Alice Student",
        "password": "student-password-123",
        "roll_number": roll_number,
        "section_id": section_id,
        "phone": "9999999999",
    }


def test_admin_can_create_student_with_backing_user(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    section = _create_section(client, headers)

    response = client.post("/api/v1/students", json=_student_payload(section["id"]), headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "student1@example.com"
    assert body["roll_number"] == "CSE2025001"
    assert body["section_id"] == section["id"]

    # The backing user was really created with the STUDENT role and can log in.
    login = client.post(
        "/api/v1/auth/login", json={"email": "student1@example.com", "password": "student-password-123"}
    )
    assert login.status_code == 200


def test_duplicate_email_returns_conflict(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    section = _create_section(client, headers)
    client.post("/api/v1/students", json=_student_payload(section["id"]), headers=headers)

    response = client.post(
        "/api/v1/students",
        json=_student_payload(section["id"], email="student1@example.com", roll_number="CSE2025002"),
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "USER_EMAIL_EXISTS"


def test_duplicate_roll_number_returns_conflict(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    section = _create_section(client, headers)
    client.post("/api/v1/students", json=_student_payload(section["id"]), headers=headers)

    response = client.post(
        "/api/v1/students",
        json=_student_payload(section["id"], email="student2@example.com", roll_number="CSE2025001"),
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "STUDENT_ROLL_NUMBER_DUPLICATE"


def test_create_student_with_missing_section_returns_404(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])

    response = client.post("/api/v1/students", json=_student_payload(999), headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SECTION_NOT_FOUND"


def test_student_role_cannot_access_student_endpoints(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    section = _create_section(client, admin_headers)
    client.post("/api/v1/students", json=_student_payload(section["id"]), headers=admin_headers)

    student_headers = make_auth_headers([RoleName.STUDENT])
    list_response = client.get("/api/v1/students", headers=student_headers)
    assert list_response.status_code == 403


def test_faculty_can_list_and_get_but_not_create_students(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    section = _create_section(client, admin_headers)
    created = client.post(
        "/api/v1/students", json=_student_payload(section["id"]), headers=admin_headers
    ).json()

    faculty_headers = make_auth_headers([RoleName.FACULTY])
    list_response = client.get("/api/v1/students", headers=faculty_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    get_response = client.get(f"/api/v1/students/{created['id']}", headers=faculty_headers)
    assert get_response.status_code == 200

    create_response = client.post(
        "/api/v1/students",
        json=_student_payload(section["id"], email="another@example.com", roll_number="CSE2025003"),
        headers=faculty_headers,
    )
    assert create_response.status_code == 403


def test_search_matches_roll_number_name_or_email(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    section = _create_section(client, headers)
    client.post(
        "/api/v1/students",
        json=_student_payload(section["id"], email="bob@example.com", roll_number="CSE2025010"),
        headers=headers,
    )

    by_roll = client.get("/api/v1/students?search=2025010", headers=headers)
    by_email = client.get("/api/v1/students?search=bob@example", headers=headers)
    by_name = client.get("/api/v1/students?search=Alice", headers=headers)

    assert by_roll.json()["total"] == 1
    assert by_email.json()["total"] == 1
    assert by_name.json()["total"] == 1


def test_section_filter_and_pagination(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    section_a = _create_section(client, headers, "Computer Science", "CSE")
    section_b = _create_section(client, headers, "Electronics", "ECE")

    for i in range(3):
        client.post(
            "/api/v1/students",
            json=_student_payload(section_a["id"], email=f"a{i}@example.com", roll_number=f"A{i}"),
            headers=headers,
        )
    client.post(
        "/api/v1/students",
        json=_student_payload(section_b["id"], email="b0@example.com", roll_number="B0"),
        headers=headers,
    )

    filtered = client.get(f"/api/v1/students?section_id={section_a['id']}", headers=headers)
    assert filtered.json()["total"] == 3

    paged = client.get(f"/api/v1/students?section_id={section_a['id']}&page=1&page_size=2", headers=headers)
    assert len(paged.json()["items"]) == 2
    assert paged.json()["total"] == 3


def test_update_student_reassigns_section_and_profile_fields(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    section_a = _create_section(client, headers, "Computer Science", "CSE")
    section_b = _create_section(client, headers, "Electronics", "ECE")
    created = client.post(
        "/api/v1/students", json=_student_payload(section_a["id"]), headers=headers
    ).json()

    response = client.patch(
        f"/api/v1/students/{created['id']}",
        json={"section_id": section_b["id"], "phone": "8888888888", "full_name": "Alice A. Student"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["section_id"] == section_b["id"]
    assert body["phone"] == "8888888888"
    assert body["full_name"] == "Alice A. Student"


def test_update_student_with_invalid_section_returns_404(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    section = _create_section(client, headers)
    created = client.post(
        "/api/v1/students", json=_student_payload(section["id"]), headers=headers
    ).json()

    response = client.patch(
        f"/api/v1/students/{created['id']}", json={"section_id": 999}, headers=headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SECTION_NOT_FOUND"


def test_deactivate_student_also_disables_login(client, make_auth_headers):
    headers = make_auth_headers([RoleName.ADMIN])
    section = _create_section(client, headers)
    created = client.post(
        "/api/v1/students", json=_student_payload(section["id"]), headers=headers
    ).json()

    response = client.delete(f"/api/v1/students/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    login = client.post(
        "/api/v1/auth/login", json={"email": "student1@example.com", "password": "student-password-123"}
    )
    assert login.status_code == 401
    assert login.json()["error"]["code"] == "INVALID_CREDENTIALS"
