from app.core.roles import RoleName


def admin_headers(make_auth_headers):
    return make_auth_headers([RoleName.ADMIN])


# ---------------------------------------------------------------------------
# Department — the representative entity: full CRUD + RBAC + validation
# exercised here in detail; other entities focus on what's genuinely
# different about them (FK checks, composite uniqueness, date rules).
# ---------------------------------------------------------------------------


def test_admin_can_create_department(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)

    response = client.post(
        "/api/v1/departments", json={"name": "Computer Science", "code": "CSE"}, headers=headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Computer Science"
    assert body["code"] == "CSE"
    assert body["is_active"] is True


def test_faculty_cannot_create_department(client, make_auth_headers):
    headers = make_auth_headers([RoleName.FACULTY])

    response = client.post(
        "/api/v1/departments", json={"name": "Physics", "code": "PHY"}, headers=headers
    )

    assert response.status_code == 403


def test_student_cannot_create_department(client, make_auth_headers):
    headers = make_auth_headers([RoleName.STUDENT])

    response = client.post(
        "/api/v1/departments", json={"name": "Physics", "code": "PHY"}, headers=headers
    )

    assert response.status_code == 403


def test_faculty_can_list_and_get_departments(client, make_auth_headers):
    admin = admin_headers(make_auth_headers)
    client.post("/api/v1/departments", json={"name": "Physics", "code": "PHY"}, headers=admin)

    faculty_headers = make_auth_headers([RoleName.FACULTY])
    list_response = client.get("/api/v1/departments", headers=faculty_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    dept_id = list_response.json()["items"][0]["id"]
    get_response = client.get(f"/api/v1/departments/{dept_id}", headers=faculty_headers)
    assert get_response.status_code == 200


def test_unauthenticated_cannot_list_departments(client):
    response = client.get("/api/v1/departments")
    assert response.status_code == 401


def test_department_get_missing_returns_404(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    response = client.get("/api/v1/departments/999", headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DEPARTMENT_NOT_FOUND"


def test_department_duplicate_name_or_code_returns_conflict(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    client.post("/api/v1/departments", json={"name": "Mathematics", "code": "MATH"}, headers=headers)

    dup_name = client.post(
        "/api/v1/departments", json={"name": "Mathematics", "code": "MATH2"}, headers=headers
    )
    dup_code = client.post(
        "/api/v1/departments", json={"name": "Applied Mathematics", "code": "MATH"}, headers=headers
    )

    assert dup_name.status_code == 409
    assert dup_code.status_code == 409
    assert dup_name.json()["error"]["code"] == "DEPARTMENT_DUPLICATE"


def test_department_update_and_deactivate(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    created = client.post(
        "/api/v1/departments", json={"name": "Chemistry", "code": "CHEM"}, headers=headers
    ).json()

    updated = client.patch(
        f"/api/v1/departments/{created['id']}", json={"name": "Chemistry Dept"}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Chemistry Dept"

    deactivated = client.delete(f"/api/v1/departments/{created['id']}", headers=headers)
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    # Deactivated row must still be fetchable (soft delete, not hard delete).
    fetched = client.get(f"/api/v1/departments/{created['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["is_active"] is False


def test_department_search_and_pagination(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    for name, code in [("Alpha Dept", "ALP"), ("Beta Dept", "BET"), ("Alpine Studies", "ALS")]:
        client.post("/api/v1/departments", json={"name": name, "code": code}, headers=headers)

    search_response = client.get("/api/v1/departments?search=alp", headers=headers)
    assert search_response.status_code == 200
    names = {item["name"] for item in search_response.json()["items"]}
    assert names == {"Alpha Dept", "Alpine Studies"}

    page_response = client.get("/api/v1/departments?page=1&page_size=2", headers=headers)
    assert page_response.status_code == 200
    body = page_response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


# ---------------------------------------------------------------------------
# Program — FK validation + department-scoped uniqueness + global code
# uniqueness.
# ---------------------------------------------------------------------------


def _create_department(client, headers, name="Computer Science", code="CSE"):
    return client.post("/api/v1/departments", json={"name": name, "code": code}, headers=headers).json()


def test_create_program_with_missing_department_returns_404(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)

    response = client.post(
        "/api/v1/programs",
        json={"name": "B.Tech CSE", "code": "BTCSE", "department_id": 999},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DEPARTMENT_NOT_FOUND"


def test_create_program_success_and_duplicate_rules(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    dept = _create_department(client, headers)

    created = client.post(
        "/api/v1/programs",
        json={"name": "B.Tech CSE", "code": "BTCSE", "department_id": dept["id"]},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["department_id"] == dept["id"]

    dup_name = client.post(
        "/api/v1/programs",
        json={"name": "B.Tech CSE", "code": "BTCSE2", "department_id": dept["id"]},
        headers=headers,
    )
    assert dup_name.status_code == 409
    assert dup_name.json()["error"]["code"] == "PROGRAM_DUPLICATE_NAME"

    dup_code = client.post(
        "/api/v1/programs",
        json={"name": "B.Tech IT", "code": "BTCSE", "department_id": dept["id"]},
        headers=headers,
    )
    assert dup_code.status_code == 409
    assert dup_code.json()["error"]["code"] == "PROGRAM_DUPLICATE_CODE"


def test_list_programs_filtered_by_department(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    dept_a = _create_department(client, headers, "Computer Science", "CSE")
    dept_b = _create_department(client, headers, "Electronics", "ECE")
    client.post(
        "/api/v1/programs",
        json={"name": "B.Tech CSE", "code": "BTCSE", "department_id": dept_a["id"]},
        headers=headers,
    )
    client.post(
        "/api/v1/programs",
        json={"name": "B.Tech ECE", "code": "BTECE", "department_id": dept_b["id"]},
        headers=headers,
    )

    response = client.get(f"/api/v1/programs?department_id={dept_a['id']}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["code"] == "BTCSE"


# ---------------------------------------------------------------------------
# Academic Year — date-order validation.
# ---------------------------------------------------------------------------


def test_academic_year_invalid_date_range_returns_422(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)

    response = client.post(
        "/api/v1/academic-years",
        json={"name": "2025-2026", "start_date": "2025-08-01", "end_date": "2025-06-01"},
        headers=headers,
    )

    assert response.status_code == 422


def test_academic_year_create_and_duplicate_name(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)

    created = client.post(
        "/api/v1/academic-years",
        json={"name": "2025-2026", "start_date": "2025-06-01", "end_date": "2026-05-31"},
        headers=headers,
    )
    assert created.status_code == 201

    dup = client.post(
        "/api/v1/academic-years",
        json={"name": "2025-2026", "start_date": "2025-07-01", "end_date": "2026-06-30"},
        headers=headers,
    )
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "ACADEMIC_YEAR_DUPLICATE"


def test_academic_year_update_rejects_invalid_resulting_range(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    year = client.post(
        "/api/v1/academic-years",
        json={"name": "2025-2026", "start_date": "2025-06-01", "end_date": "2026-05-31"},
        headers=headers,
    ).json()

    # Only updating start_date to something after the existing end_date —
    # schema-level validator can't catch this (end_date isn't in the
    # payload), so this proves the service-level re-check works too.
    response = client.patch(
        f"/api/v1/academic-years/{year['id']}", json={"start_date": "2027-01-01"}, headers=headers
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


# ---------------------------------------------------------------------------
# Semester — FK validation + must fall within parent academic year's range.
# ---------------------------------------------------------------------------


def _create_academic_year(client, headers, name="2025-2026"):
    return client.post(
        "/api/v1/academic-years",
        json={"name": name, "start_date": "2025-06-01", "end_date": "2026-05-31"},
        headers=headers,
    ).json()


def test_create_semester_with_missing_academic_year_returns_404(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)

    response = client.post(
        "/api/v1/semesters",
        json={
            "name": "Semester 1",
            "academic_year_id": 999,
            "start_date": "2025-06-01",
            "end_date": "2025-11-30",
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ACADEMIC_YEAR_NOT_FOUND"


def test_semester_dates_outside_academic_year_rejected(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    year = _create_academic_year(client, headers)

    response = client.post(
        "/api/v1/semesters",
        json={
            "name": "Semester 1",
            "academic_year_id": year["id"],
            "start_date": "2025-01-01",
            "end_date": "2025-05-01",
        },
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SEMESTER_OUTSIDE_ACADEMIC_YEAR"


def test_semester_create_and_duplicate_name_within_year(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    year = _create_academic_year(client, headers)

    created = client.post(
        "/api/v1/semesters",
        json={
            "name": "Semester 1",
            "academic_year_id": year["id"],
            "start_date": "2025-06-01",
            "end_date": "2025-11-30",
        },
        headers=headers,
    )
    assert created.status_code == 201

    dup = client.post(
        "/api/v1/semesters",
        json={
            "name": "Semester 1",
            "academic_year_id": year["id"],
            "start_date": "2025-12-01",
            "end_date": "2026-04-30",
        },
        headers=headers,
    )
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "SEMESTER_DUPLICATE"


# ---------------------------------------------------------------------------
# Class — FK validation + program-scoped uniqueness.
# ---------------------------------------------------------------------------


def _create_program(client, headers, name="B.Tech CSE", code="BTCSE"):
    dept = _create_department(client, headers)
    return client.post(
        "/api/v1/programs",
        json={"name": name, "code": code, "department_id": dept["id"]},
        headers=headers,
    ).json()


def test_create_class_with_missing_program_returns_404(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)

    response = client.post(
        "/api/v1/classes", json={"name": "First Year", "program_id": 999}, headers=headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROGRAM_NOT_FOUND"


def test_class_create_and_duplicate_name_within_program(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    program = _create_program(client, headers)

    created = client.post(
        "/api/v1/classes", json={"name": "First Year", "program_id": program["id"]}, headers=headers
    )
    assert created.status_code == 201

    dup = client.post(
        "/api/v1/classes", json={"name": "First Year", "program_id": program["id"]}, headers=headers
    )
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "CLASS_DUPLICATE"


# ---------------------------------------------------------------------------
# Section — FK validation + class-scoped uniqueness + capacity validation.
# ---------------------------------------------------------------------------


def _create_class(client, headers, name="First Year"):
    program = _create_program(client, headers)
    return client.post(
        "/api/v1/classes", json={"name": name, "program_id": program["id"]}, headers=headers
    ).json()


def test_create_section_with_missing_class_returns_404(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)

    response = client.post(
        "/api/v1/sections", json={"name": "A", "class_id": 999}, headers=headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CLASS_NOT_FOUND"


def test_section_create_and_duplicate_name_within_class(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    academic_class = _create_class(client, headers)

    created = client.post(
        "/api/v1/sections",
        json={"name": "A", "class_id": academic_class["id"], "capacity": 60},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["capacity"] == 60

    dup = client.post(
        "/api/v1/sections", json={"name": "A", "class_id": academic_class["id"]}, headers=headers
    )
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "SECTION_DUPLICATE"


def test_section_invalid_capacity_rejected(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    academic_class = _create_class(client, headers)

    response = client.post(
        "/api/v1/sections",
        json={"name": "B", "class_id": academic_class["id"], "capacity": 0},
        headers=headers,
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Subject — FK validation + globally-unique code.
# ---------------------------------------------------------------------------


def test_create_subject_with_missing_department_returns_404(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)

    response = client.post(
        "/api/v1/subjects",
        json={"name": "Data Structures", "code": "CS201", "department_id": 999},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DEPARTMENT_NOT_FOUND"


def test_subject_create_and_duplicate_code(client, make_auth_headers):
    headers = admin_headers(make_auth_headers)
    dept = _create_department(client, headers)

    created = client.post(
        "/api/v1/subjects",
        json={"name": "Data Structures", "code": "CS201", "department_id": dept["id"], "credits": 4},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["credits"] == 4

    dup = client.post(
        "/api/v1/subjects",
        json={"name": "Algorithms", "code": "CS201", "department_id": dept["id"]},
        headers=headers,
    )
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "SUBJECT_DUPLICATE_CODE"
