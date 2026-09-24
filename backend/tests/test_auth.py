from datetime import timedelta

from app.core.security import create_access_token
from app.services import auth_service

TEST_PASSWORD = "correct-horse-battery-staple"


def _create_test_user(db_session, *, email="user@example.com", is_active=True):
    user = auth_service.create_user(
        db_session, email=email, full_name="Test User", password=TEST_PASSWORD
    )
    if not is_active:
        user.is_active = False
        db_session.commit()
        db_session.refresh(user)
    return user


def test_login_with_valid_credentials_returns_token(client, db_session):
    _create_test_user(db_session)

    response = client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": TEST_PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


def test_login_with_wrong_password_returns_invalid_credentials(client, db_session):
    _create_test_user(db_session)

    response = client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_with_unknown_email_returns_same_invalid_credentials_error(client, db_session):
    _create_test_user(db_session)

    response = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": TEST_PASSWORD}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert response.json()["error"]["message"] == auth_service.INVALID_CREDENTIALS_MESSAGE


def test_login_with_inactive_user_is_rejected(client, db_session):
    _create_test_user(db_session, is_active=False)

    response = client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": TEST_PASSWORD}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_protected_endpoint_without_token_returns_missing_token(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MISSING_TOKEN"


def test_protected_endpoint_with_malformed_token_returns_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_protected_endpoint_with_expired_token_returns_token_expired(client):
    expired_token = create_access_token(subject="1", expires_delta=timedelta(minutes=-5))

    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_protected_endpoint_with_valid_token_returns_user_profile(client, db_session):
    user = _create_test_user(db_session)
    token = auth_service.issue_token_for_user(user)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["full_name"] == "Test User"
    assert "password" not in body
    assert "hashed_password" not in body
    assert body["roles"] == []  # this user has no roles assigned


def test_current_user_profile_includes_roles(client, db_session):
    from app.core.roles import RoleName
    from app.services import user_service

    user = user_service.create_user_with_roles(
        db_session,
        email="roled@example.com",
        full_name="Roled User",
        password=TEST_PASSWORD,
        role_names=[RoleName.ADMIN, RoleName.FACULTY],
    )
    token = auth_service.issue_token_for_user(user)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert set(response.json()["roles"]) == {"ADMIN", "FACULTY"}


def test_current_user_profile_has_null_student_and_faculty_id_by_default(client, db_session):
    user = _create_test_user(db_session)
    token = auth_service.issue_token_for_user(user)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["student_id"] is None
    assert body["faculty_id"] is None


def test_current_user_profile_includes_own_student_id(client, make_auth_headers):
    from app.core.roles import RoleName

    admin_headers = make_auth_headers([RoleName.ADMIN])
    dept = client.post("/api/v1/departments", json={"name": "CS Me", "code": "CSME"}, headers=admin_headers).json()
    program = client.post(
        "/api/v1/programs",
        json={"name": "B.Tech", "code": "BTME", "department_id": dept["id"]},
        headers=admin_headers,
    ).json()
    academic_class = client.post(
        "/api/v1/classes", json={"name": "Year 1", "program_id": program["id"]}, headers=admin_headers
    ).json()
    section = client.post(
        "/api/v1/sections", json={"name": "A", "class_id": academic_class["id"]}, headers=admin_headers
    ).json()
    student = client.post(
        "/api/v1/students",
        json={
            "email": "me-student@example.com",
            "full_name": "Me Student",
            "password": "student-password-123",
            "roll_number": "ME2025001",
            "section_id": section["id"],
        },
        headers=admin_headers,
    ).json()

    login_response = client.post(
        "/api/v1/auth/login", json={"email": "me-student@example.com", "password": "student-password-123"}
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["student_id"] == student["id"]
    assert body["faculty_id"] is None


def test_current_user_profile_includes_own_faculty_id(client, make_auth_headers):
    from app.core.roles import RoleName

    admin_headers = make_auth_headers([RoleName.ADMIN])
    dept = client.post("/api/v1/departments", json={"name": "CS Me2", "code": "CSME2"}, headers=admin_headers).json()
    faculty = client.post(
        "/api/v1/faculty",
        json={
            "email": "me-faculty@example.com",
            "full_name": "Me Faculty",
            "password": "faculty-password-123",
            "employee_id": "EMP-ME-1",
            "department_id": dept["id"],
        },
        headers=admin_headers,
    ).json()

    login_response = client.post(
        "/api/v1/auth/login", json={"email": "me-faculty@example.com", "password": "faculty-password-123"}
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["faculty_id"] == faculty["id"]
    assert body["student_id"] is None


def test_logout_revokes_token_so_it_can_no_longer_be_used(client, db_session):
    user = _create_test_user(db_session)
    token = auth_service.issue_token_for_user(user)
    headers = {"Authorization": f"Bearer {token}"}

    logout_response = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    assert logout_response.json()["success"] is True

    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 401
    assert me_response.json()["error"]["code"] == "TOKEN_REVOKED"


def test_logout_without_token_returns_missing_token(client):
    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MISSING_TOKEN"
