from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import token_repository, user_repository

INVALID_CREDENTIALS_MESSAGE = "Incorrect email or password."


def authenticate(db: Session, *, email: str, password: str) -> User:
    """Raises the identical error for unknown email, wrong password, and
    inactive user — deliberately, to avoid leaking which case occurred
    (user enumeration prevention, see AC2/AC3/AC9 in
    docs/sdd/02-authentication-spec.md)."""
    user = user_repository.get_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise UnauthorizedError(INVALID_CREDENTIALS_MESSAGE, code="INVALID_CREDENTIALS")
    if not user.is_active:
        raise UnauthorizedError(INVALID_CREDENTIALS_MESSAGE, code="INVALID_CREDENTIALS")
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
