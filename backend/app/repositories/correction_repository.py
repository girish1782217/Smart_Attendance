from sqlalchemy.orm import Session, joinedload

from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession
from app.models.correction_request import CorrectionRequest, CorrectionRequestStatus
from app.models.student import Student

_EAGER = (
    joinedload(CorrectionRequest.attendance_record).joinedload(AttendanceRecord.student).joinedload(Student.user),
    joinedload(CorrectionRequest.requested_by),
    joinedload(CorrectionRequest.reviewed_by),
)


def get_by_id(db: Session, correction_id: int) -> CorrectionRequest | None:
    return (
        db.query(CorrectionRequest).options(*_EAGER).filter(CorrectionRequest.id == correction_id).first()
    )


def get_pending_for_record(db: Session, attendance_record_id: int) -> CorrectionRequest | None:
    return (
        db.query(CorrectionRequest)
        .filter(
            CorrectionRequest.attendance_record_id == attendance_record_id,
            CorrectionRequest.status == CorrectionRequestStatus.PENDING,
        )
        .first()
    )


def list_paginated(
    db: Session,
    *,
    page: int,
    page_size: int,
    status: CorrectionRequestStatus | None = None,
    attendance_record_id: int | None = None,
    faculty_id: int | None = None,
    student_id: int | None = None,
) -> tuple[list[CorrectionRequest], int]:
    query = db.query(CorrectionRequest).join(
        AttendanceRecord, CorrectionRequest.attendance_record_id == AttendanceRecord.id
    )

    if faculty_id is not None:
        query = query.join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id).filter(
            AttendanceSession.faculty_id == faculty_id
        )
    if student_id is not None:
        query = query.filter(AttendanceRecord.student_id == student_id)
    if status is not None:
        query = query.filter(CorrectionRequest.status == status)
    if attendance_record_id is not None:
        query = query.filter(CorrectionRequest.attendance_record_id == attendance_record_id)

    query = query.options(*_EAGER)
    total = query.count()
    items = (
        query.order_by(CorrectionRequest.requested_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def create(db: Session, correction: CorrectionRequest) -> CorrectionRequest:
    db.add(correction)
    db.commit()
    db.refresh(correction)
    return correction
