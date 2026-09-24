from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.core.roles import RoleName
from app.models.user import User
from app.repositories import faculty_repository, student_repository


def _is_admin(current_user: User) -> bool:
    return RoleName.ADMIN.value in {role.name for role in current_user.roles}


def _resolve_own_faculty_id(db: Session, current_user: User) -> int:
    faculty = faculty_repository.get_by_user_id(db, current_user.id)
    if faculty is None:
        raise NotFoundError(
            "No faculty profile is linked to the current user.", code="FACULTY_PROFILE_NOT_FOUND"
        )
    return faculty.id


def resolve_own_student_id(db: Session, current_user: User) -> int:
    student = student_repository.get_by_user_id(db, current_user.id)
    if student is None:
        raise NotFoundError(
            "No student profile is linked to the current user.", code="STUDENT_PROFILE_NOT_FOUND"
        )
    return student.id


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


def resolve_student_access_scope(db: Session, current_user: User, student_id: int) -> int | None:
    """For endpoints that read one student's data (attendance summary/
    history, AI insight): returns the faculty_id to scope records by, or
    None for "no restriction" (ADMIN, or STUDENT viewing their own — a
    student sees all their own subjects, not just one faculty's). Raises
    403 for a STUDENT requesting someone else's data, or any other role
    with no valid access path."""
    roles = {role.name for role in current_user.roles}
    if RoleName.ADMIN.value in roles:
        return None
    if RoleName.STUDENT.value in roles:
        own_student_id = resolve_own_student_id(db, current_user)
        if own_student_id != student_id:
            raise ForbiddenError("You can only view your own data.", code="FORBIDDEN")
        return None
    if RoleName.FACULTY.value in roles:
        return resolve_faculty_filter(db, current_user, None)
    raise ForbiddenError("You do not have permission to perform this action.", code="FORBIDDEN")
