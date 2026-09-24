from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.attendance_session import AttendanceSession
from app.models.user import User
from app.schemas.attendance_record import AttendanceRecordResponse, BulkMarkRequest
from app.schemas.attendance_session import AttendanceSessionCreateRequest, AttendanceSessionResponse
from app.schemas.pagination import Page, PaginationParams
from app.schemas.student import StudentResponse
from app.services import attendance_record_service, attendance_session_service, scoping

router = APIRouter(prefix="/attendance-sessions", tags=["attendance-sessions"])


def _check_access(db: Session, current_user: User, session: AttendanceSession) -> None:
    effective_faculty_id = scoping.resolve_faculty_filter(db, current_user, None)
    attendance_session_service.ensure_faculty_can_access(effective_faculty_id, session)


@router.post("", response_model=AttendanceSessionResponse, status_code=201)
def create_session(
    payload: AttendanceSessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> AttendanceSessionResponse:
    faculty_id = scoping.resolve_faculty_for_write(db, current_user, payload.faculty_id)
    session = attendance_session_service.create_session(
        db,
        faculty_id=faculty_id,
        subject_id=payload.subject_id,
        section_id=payload.section_id,
        session_date=payload.session_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    return AttendanceSessionResponse.from_model(session)


@router.get("", response_model=Page[AttendanceSessionResponse])
def list_sessions(
    pagination: PaginationParams = Depends(),
    faculty_id: int | None = None,
    section_id: int | None = None,
    subject_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> Page[AttendanceSessionResponse]:
    effective_faculty_id = scoping.resolve_faculty_filter(db, current_user, faculty_id)
    items, total = attendance_session_service.list_sessions(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        faculty_id=effective_faculty_id,
        section_id=section_id,
        subject_id=subject_id,
        from_date=from_date,
        to_date=to_date,
    )
    return Page(
        items=[AttendanceSessionResponse.from_model(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{session_id}", response_model=AttendanceSessionResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> AttendanceSessionResponse:
    session = attendance_session_service.get_session(db, session_id)
    _check_access(db, current_user, session)
    return AttendanceSessionResponse.from_model(session)


@router.get("/{session_id}/roster", response_model=list[StudentResponse])
def get_roster(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> list[StudentResponse]:
    session = attendance_session_service.get_session(db, session_id)
    _check_access(db, current_user, session)
    students = attendance_session_service.get_roster(db, session_id)
    return [StudentResponse.from_model(student) for student in students]


@router.put("/{session_id}/records", response_model=list[AttendanceRecordResponse])
def bulk_mark_records(
    session_id: int,
    payload: BulkMarkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> list[AttendanceRecordResponse]:
    session = attendance_session_service.get_session(db, session_id)
    _check_access(db, current_user, session)
    records = attendance_record_service.bulk_mark(
        db,
        session_id=session_id,
        items=[(item.student_id, item.status) for item in payload.records],
        recorded_by_user_id=current_user.id,
    )
    return [AttendanceRecordResponse.from_model(record) for record in records]


@router.get("/{session_id}/records", response_model=list[AttendanceRecordResponse])
def list_records(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> list[AttendanceRecordResponse]:
    session = attendance_session_service.get_session(db, session_id)
    _check_access(db, current_user, session)
    records = attendance_record_service.list_records(db, session_id)
    return [AttendanceRecordResponse.from_model(record) for record in records]


@router.post("/{session_id}/submit", response_model=AttendanceSessionResponse)
def submit_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> AttendanceSessionResponse:
    session = attendance_session_service.get_session(db, session_id)
    _check_access(db, current_user, session)
    submitted = attendance_record_service.submit_session(db, session_id)
    return AttendanceSessionResponse.from_model(submitted)
