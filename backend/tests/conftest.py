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
