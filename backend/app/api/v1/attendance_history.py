from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.core.roles import RoleName
from app.models.user import User
from app.schemas.attendance_history import (
    AttendanceHistoryRecordResponse,
    StudentAttendanceSummaryResponse,
)
from app.schemas.pagination import Page, PaginationParams
from app.services import attendance_history_service, scoping

router = APIRouter(prefix="/students", tags=["attendance-history"])


def _resolve_faculty_scope(db: Session, current_user: User, student_id: int) -> int | None:
    """Returns the faculty_id to scope records by, or None for "no
    restriction" (ADMIN, or STUDENT viewing their own — a student sees all
    subjects for themself). Raises 403 for anyone not authorized at all."""
    roles = {role.name for role in current_user.roles}
    if RoleName.ADMIN.value in roles:
        return None
    if RoleName.STUDENT.value in roles:
        own_student_id = scoping.resolve_own_student_id(db, current_user)
        if own_student_id != student_id:
            raise ForbiddenError("You can only view your own attendance history.", code="FORBIDDEN")
        return None
    if RoleName.FACULTY.value in roles:
        return scoping.resolve_faculty_filter(db, current_user, None)
    raise ForbiddenError("You do not have permission to perform this action.", code="FORBIDDEN")


@router.get("/{student_id}/attendance-summary", response_model=StudentAttendanceSummaryResponse)
def get_attendance_summary(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY, RoleName.STUDENT)),
) -> StudentAttendanceSummaryResponse:
    faculty_scope = _resolve_faculty_scope(db, current_user, student_id)
    summary = attendance_history_service.get_summary(db, student_id=student_id, faculty_id=faculty_scope)
    return StudentAttendanceSummaryResponse.model_validate(summary)


@router.get("/{student_id}/attendance-history", response_model=Page[AttendanceHistoryRecordResponse])
def get_attendance_history(
    student_id: int,
    pagination: PaginationParams = Depends(),
    subject_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY, RoleName.STUDENT)),
) -> Page[AttendanceHistoryRecordResponse]:
    faculty_scope = _resolve_faculty_scope(db, current_user, student_id)
    records, corrections_by_record_id, total = attendance_history_service.get_history(
        db,
        student_id=student_id,
        subject_id=subject_id,
        faculty_id=faculty_scope,
        from_date=from_date,
        to_date=to_date,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    items = [
        AttendanceHistoryRecordResponse.from_model(record, corrections_by_record_id.get(record.id))
        for record in records
    ]
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
