from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.roles import RoleName
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories import token_repository, user_repository
from app.services import gemini_client

bearer_scheme = HTTPBearer(auto_error=False)


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise UnauthorizedError("Authentication required.", code="MISSING_TOKEN")
    return credentials.credentials


def get_current_user(
    token: str = Depends(get_bearer_token),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)

    if token_repository.is_revoked(db, payload["jti"]):
        raise UnauthorizedError("Token has been revoked.", code="TOKEN_REVOKED")

    user = user_repository.get_by_id(db, int(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive.", code="INVALID_TOKEN")

    return user


def get_gemini_generate_fn() -> Callable[[str], str]:
    """Returns the function used to call Gemini. Tests override this via
    `app.dependency_overrides[get_gemini_generate_fn] = lambda: fake_fn` so
    no automated test ever needs network access or a real API key."""
    return gemini_client.generate_content


def require_role(*allowed_roles: RoleName):
    """Dependency factory gating an endpoint to one or more roles.

    Roles are read from the DB-backed `current_user.roles` relationship
    (not a JWT claim), so a role change takes effect on the very next
    request rather than requiring re-login.
    """
    allowed_names = {role.value for role in allowed_roles}

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        user_role_names = {role.name for role in current_user.roles}
        if not user_role_names & allowed_names:
            raise ForbiddenError(
                "You do not have permission to perform this action.", code="FORBIDDEN"
            )
        return current_user

    return _dependency
