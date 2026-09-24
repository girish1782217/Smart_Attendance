from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import TooManyRequestsError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import token_repository, user_repository
from app.services import rate_limit_service

INVALID_CREDENTIALS_MESSAGE = "Incorrect email or password."


def authenticate(db: Session, *, email: str, password: str) -> User:
    """Raises the identical error for unknown email, wrong password, and
    inactive user — deliberately, to avoid leaking which case occurred
    (user enumeration prevention, see AC2/AC3/AC9 in
    docs/sdd/02-authentication-spec.md). Also rate-limited per email (SPEC
    16): 5 failed attempts within the window -> 429, reset on success."""
    if rate_limit_service.is_rate_limited(email):
        raise TooManyRequestsError(
            "Too many failed login attempts. Please try again later.", code="RATE_LIMITED"
        )

    user = user_repository.get_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        rate_limit_service.register_failed_attempt(email)
        raise UnauthorizedError(INVALID_CREDENTIALS_MESSAGE, code="INVALID_CREDENTIALS")
    if not user.is_active:
        rate_limit_service.register_failed_attempt(email)
        raise UnauthorizedError(INVALID_CREDENTIALS_MESSAGE, code="INVALID_CREDENTIALS")

    rate_limit_service.clear_attempts(email)
    return user


def issue_token_for_user(user: User) -> str:
    return create_access_token(subject=str(user.id))


def create_user(db: Session, *, email: str, full_name: str, password: str) -> User:
    return user_repository.create(
        db,
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
    )


def logout(db: Session, *, payload: dict) -> None:
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None)
    token_repository.revoke(db, jti=payload["jti"], expires_at=expires_at)
