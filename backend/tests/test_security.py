import pytest

from app.core.config import INSECURE_DEFAULT_JWT_SECRET, Settings, validate_production_settings
from app.core.roles import RoleName


def _create_test_user(client, db_session, email="ratelimit@example.com", password="correct-password-123"):
    from app.services import auth_service

    return auth_service.create_user(db_session, email=email, full_name="Rate Limit Test", password=password)


def test_five_failed_logins_then_rate_limited(client, db_session):
    email = "ratelimit1@example.com"
    _create_test_user(client, db_session, email=email)

    for _ in range(5):
        response = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-password"})
        assert response.status_code == 401

    sixth_attempt = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "correct-password-123"}
    )

    assert sixth_attempt.status_code == 429
    assert sixth_attempt.json()["error"]["code"] == "RATE_LIMITED"


def test_successful_login_clears_the_counter(client, db_session):
    email = "ratelimit2@example.com"
    _create_test_user(client, db_session, email=email, password="correct-password-123")

    for _ in range(3):
        client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-password"})

    success = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "correct-password-123"}
    )
    assert success.status_code == 200

    # Counter reset -- another 3 failures shouldn't trip the 5-attempt limit.
    for _ in range(3):
        response = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-password"})
        assert response.status_code == 401  # not yet 429


def test_rate_limiting_is_scoped_per_email(client, db_session):
    email_a = "ratelimit-a@example.com"
    email_b = "ratelimit-b@example.com"
    _create_test_user(client, db_session, email=email_a)
    _create_test_user(client, db_session, email=email_b)

    for _ in range(5):
        client.post("/api/v1/auth/login", json={"email": email_a, "password": "wrong-password"})

    # email_a is now rate-limited, but email_b is unaffected.
    response_b = client.post(
        "/api/v1/auth/login", json={"email": email_b, "password": "correct-password-123"}
    )
    assert response_b.status_code == 200


def test_security_headers_present_on_every_response(client):
    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_production_with_insecure_default_secret_raises():
    settings = Settings(
        environment="production",
        jwt_secret=INSECURE_DEFAULT_JWT_SECRET,
        database_url="sqlite:///:memory:",
    )

    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_settings(settings)


def test_production_with_custom_secret_does_not_raise():
    settings = Settings(
        environment="production",
        jwt_secret="a-real-randomly-generated-secret",
        database_url="sqlite:///:memory:",
    )

    validate_production_settings(settings)  # must not raise


def test_development_with_default_secret_does_not_raise():
    settings = Settings(
        environment="development",
        jwt_secret=INSECURE_DEFAULT_JWT_SECRET,
        database_url="sqlite:///:memory:",
    )

    validate_production_settings(settings)  # must not raise -- dev is fine


def test_search_with_sql_injection_style_payload_is_handled_safely(client, make_auth_headers):
    admin_headers = make_auth_headers([RoleName.ADMIN])
    client.post("/api/v1/departments", json={"name": "Computer Science", "code": "CSE"}, headers=admin_headers)

    malicious_search = "'; DROP TABLE departments; --"
    response = client.get(
        f"/api/v1/departments?search={malicious_search}", headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0  # treated as a literal (non-matching) string

    # Prove the table really wasn't dropped -- a normal search still works.
    follow_up = client.get("/api/v1/departments?search=Computer", headers=admin_headers)
    assert follow_up.status_code == 200
    assert follow_up.json()["total"] == 1
