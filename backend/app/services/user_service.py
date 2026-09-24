from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.core.roles import RoleName
from app.core.security import hash_password
from app.models.user import User
from app.repositories import role_repository, user_repository


def _resolve_roles(db: Session, role_names: list[RoleName]):
    roles = role_repository.get_by_names(db, [name.value for name in role_names])
    if len(roles) != len(set(role_names)):
        raise ValidationAppError("One or more role names are invalid.", code="INVALID_ROLE")
    return roles


def create_user_with_roles(
    db: Session,
    *,
    email: str,
    full_name: str,
    password: str,
    role_names: list[RoleName],
) -> User:
    if user_repository.get_by_email(db, email) is not None:
        raise ConflictError("A user with this email already exists.", code="USER_EMAIL_EXISTS")

    roles = _resolve_roles(db, role_names)

    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        is_active=True,
    )
    user.roles = roles
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, *, page: int, page_size: int) -> tuple[list[User], int]:
    return user_repository.list_users(db, page=page, page_size=page_size)


def set_user_roles(db: Session, *, user_id: int, role_names: list[RoleName]) -> User:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User not found.", code="USER_NOT_FOUND")

    user.roles = _resolve_roles(db, role_names)
    db.commit()
    db.refresh(user)
    return user
