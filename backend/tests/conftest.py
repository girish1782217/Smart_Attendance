import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.roles import RoleName
from app.main import create_app
from app.models.role import Role

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """rate_limit_service (SPEC 16) keeps process-global in-memory state,
    independent of the per-test DB — without this it would leak failed-
    login counts across every test in the suite that touches /auth/login."""
    from app.services import rate_limit_service

    rate_limit_service.reset_all()
    yield
    rate_limit_service.reset_all()


@pytest.fixture()
def db_session():
    """A fresh, isolated in-memory SQLite DB for a single test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = testing_session_local()
    # `create_all` builds schema only — it does not run the Alembic
    # migration's data seed, so the 3 fixed system roles are seeded here
    # instead, once per test, for every test that needs a role-bearing user.
    session.add_all(Role(name=role.value) for role in RoleName)
    session.commit()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """A FastAPI TestClient wired to the isolated test DB."""
    app = create_app()

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_auth_headers(client, db_session):
    """Factory fixture: make_auth_headers([RoleName.ADMIN]) creates a fresh
    user with those roles, logs in via the real endpoint, and returns
    ready-to-use Authorization headers. Shared across test modules so every
    future spec's tests don't re-derive this."""
    from app.services import auth_service, user_service

    password = "test-password-123"  # noqa: S105 (test fixture, not a real credential)
    counter = {"value": 0}

    def _make(role_names: list[RoleName]) -> dict:
        counter["value"] += 1
        email = f"fixture-user-{counter['value']}@example.com"
        user_service.create_user_with_roles(
            db_session, email=email, full_name="Fixture User", password=password, role_names=role_names
        )
        response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make
