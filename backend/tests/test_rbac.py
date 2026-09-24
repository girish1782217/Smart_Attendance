from fastapi import Depends
from fastapi.testclient import TestClient

from app.api.deps import require_role
from app.core.roles import RoleName
from app.main import create_app
from app.services import user_service

PASSWORD = "correct-horse-battery-staple"


def _create_user(db_session, email, role_names):
    return user_service.create_user_with_roles(
        db_session, email=email, full_name="Test User", password=PASSWORD, role_names=role_names
    )


def _login(client, email):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_create_user_and_assign_role(client, db_session):
    _create_user(db_session, "admin@example.com", [RoleName.ADMIN])
    token = _login(client, "admin@example.com")

    response = client.post(
        "/api/v1/users",
        json={
            "email": "newfaculty@example.com",
            "full_name": "New Faculty",
            "password": "another-strong-password",
            "role_names": ["FACULTY"],
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newfaculty@example.com"
    assert body["roles"] == ["FACULTY"]


def test_faculty_cannot_create_user(client, db_session):
    _create_user(db_session, "faculty@example.com", [RoleName.FACULTY])
    token = _login(client, "faculty@example.com")

    response = client.post(
        "/api/v1/users",
        json={
            "email": "x@example.com",
            "full_name": "X",
            "password": "another-strong-password",
            "role_names": ["STUDENT"],
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_student_cannot_create_user(client, db_session):
    _create_user(db_session, "student@example.com", [RoleName.STUDENT])
    token = _login(client, "student@example.com")

    response = client.post(
        "/api/v1/users",
        json={
            "email": "y@example.com",
            "full_name": "Y",
            "password": "another-strong-password",
            "role_names": ["STUDENT"],
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_unauthenticated_request_returns_401_not_403(client):
    response = client.post(
        "/api/v1/users",
        json={
            "email": "z@example.com",
            "full_name": "Z",
            "password": "another-strong-password",
            "role_names": ["STUDENT"],
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MISSING_TOKEN"


def test_admin_can_list_users_with_pagination(client, db_session):
    _create_user(db_session, "admin2@example.com", [RoleName.ADMIN])
    for i in range(3):
        _create_user(db_session, f"student{i}@example.com", [RoleName.STUDENT])
    token = _login(client, "admin2@example.com")

    response = client.get("/api/v1/users?page=1&page_size=2", headers=_auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 4
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 2


def test_admin_can_assign_multiple_roles(client, db_session):
    _create_user(db_session, "admin3@example.com", [RoleName.ADMIN])
    target = _create_user(db_session, "multi@example.com", [RoleName.FACULTY])
    token = _login(client, "admin3@example.com")

    response = client.put(
        f"/api/v1/users/{target.id}/roles",
        json={"role_names": ["FACULTY", "ADMIN"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert set(response.json()["roles"]) == {"FACULTY", "ADMIN"}


def test_create_user_with_duplicate_email_returns_conflict(client, db_session):
    _create_user(db_session, "admin4@example.com", [RoleName.ADMIN])
    _create_user(db_session, "dupe@example.com", [RoleName.STUDENT])
    token = _login(client, "admin4@example.com")

    response = client.post(
        "/api/v1/users",
        json={
            "email": "dupe@example.com",
            "full_name": "Dup",
            "password": "another-strong-password",
            "role_names": ["STUDENT"],
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "USER_EMAIL_EXISTS"


def test_create_user_with_invalid_role_name_is_rejected_by_schema(client, db_session):
    _create_user(db_session, "admin5@example.com", [RoleName.ADMIN])
    token = _login(client, "admin5@example.com")

    response = client.post(
        "/api/v1/users",
        json={
            "email": "bad@example.com",
            "full_name": "Bad",
            "password": "another-strong-password",
            "role_names": ["SUPERUSER"],
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


def test_require_role_grants_access_to_any_of_several_allowed_roles(client, db_session):
    """Proves require_role's "any of several roles" support independent of
    the /users endpoints, which only ever require a single role."""
    app = create_app()

    @app.get("/__test/multi-role")
    def _multi_role_endpoint(_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY))):
        return {"ok": True}

    def _override_get_db():
        yield db_session

    from app.core.database import get_db

    app.dependency_overrides[get_db] = _override_get_db

    _create_user(db_session, "faculty2@example.com", [RoleName.FACULTY])
    _create_user(db_session, "student2@example.com", [RoleName.STUDENT])

    with TestClient(app) as test_client:
        faculty_token = _login(test_client, "faculty2@example.com")
        student_token = _login(test_client, "student2@example.com")

        faculty_response = test_client.get(
            "/__test/multi-role", headers=_auth_headers(faculty_token)
        )
        student_response = test_client.get(
            "/__test/multi-role", headers=_auth_headers(student_token)
        )

    assert faculty_response.status_code == 200
    assert student_response.status_code == 403
