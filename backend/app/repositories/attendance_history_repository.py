from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession


def _base_query(
    db: Session,
    *,
    student_id: int,
    subject_id: int | None,
    faculty_id: int | None,
    from_date: date | None = None,
    to_date: date | None = None,
):
    query = (
        db.query(AttendanceRecord)
        .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)
        .filter(AttendanceRecord.student_id == student_id)
    )
    if subject_id is not None:
        query = query.filter(AttendanceSession.subject_id == subject_id)
    if faculty_id is not None:
        query = query.filter(AttendanceSession.faculty_id == faculty_id)
    if from_date is not None:
        query = query.filter(AttendanceSession.session_date >= from_date)
    if to_date is not None:
        query = query.filter(AttendanceSession.session_date <= to_date)
    return query


def list_all_for_summary(
    db: Session, *, student_id: int, faculty_id: int | None = None
) -> list[AttendanceRecord]:
    """Unpaginated on purpose — percentage calculation needs every
    applicable record, not one page of them. Bounded by one student's
    actual session count, never a cross-student aggregate."""
    return (
        _base_query(db, student_id=student_id, subject_id=None, faculty_id=faculty_id)
        .options(
            joinedload(AttendanceRecord.session).joinedload(AttendanceSession.subject)
        )
        .all()
    )


def list_paginated(
    db: Session,
    *,
    student_id: int,
    subject_id: int | None,
    faculty_id: int | None,
    from_date: date | None,
    to_date: date | None,
    page: int,
    page_size: int,
) -> tuple[list[AttendanceRecord], int]:
    query = _base_query(
        db,
        student_id=student_id,
        subject_id=subject_id,
        faculty_id=faculty_id,
        from_date=from_date,
        to_date=to_date,
    ).options(joinedload(AttendanceRecord.session).joinedload(AttendanceSession.subject))

    total = query.count()
    items = (
        query.order_by(AttendanceSession.session_date.desc(), AttendanceSession.start_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total
