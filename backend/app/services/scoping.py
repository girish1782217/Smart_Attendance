from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.roles import RoleName
from app.models.user import User
from app.repositories import faculty_repository


def _is_admin(current_user: User) -> bool:
    return RoleName.ADMIN.value in {role.name for role in current_user.roles}


def _resolve_own_faculty_id(db: Session, current_user: User) -> int:
    faculty = faculty_repository.get_by_user_id(db, current_user.id)
    if faculty is None:
        raise NotFoundError(
            "No faculty profile is linked to the current user.", code="FACULTY_PROFILE_NOT_FOUND"
        )
    return faculty.id


def resolve_faculty_filter(
    db: Session, current_user: User, requested_faculty_id: int | None
) -> int | None:
    """For read/list endpoints: ADMIN may filter by any faculty_id (or None,
    meaning "everyone"). Any other caller is always scoped to their own
    linked Faculty id, regardless of what they pass — the param is
    overridden, not merely validated, so there's no way to browse another
    faculty member's data by guessing an id."""
    if _is_admin(current_user):
        return requested_faculty_id
    return _resolve_own_faculty_id(db, current_user)


def resolve_faculty_for_write(
    db: Session, current_user: User, requested_faculty_id: int | None
) -> int:
    """For create endpoints acting on behalf of exactly one faculty member:
    ADMIN must supply requested_faculty_id explicitly (there's no "own" one
    to default to); any other caller is always resolved to their own."""
    if _is_admin(current_user):
        if requested_faculty_id is None:
            raise ValidationAppError("faculty_id is required.", code="FACULTY_ID_REQUIRED")
        return requested_faculty_id
    return _resolve_own_faculty_id(db, current_user)
