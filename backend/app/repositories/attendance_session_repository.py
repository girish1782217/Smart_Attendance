from datetime import date, time

from sqlalchemy.orm import Session, joinedload

from app.models.attendance_session import AttendanceSession
from app.models.faculty import Faculty

_EAGER = (
    joinedload(AttendanceSession.faculty).joinedload(Faculty.user),
    joinedload(AttendanceSession.subject),
    joinedload(AttendanceSession.section),
)


def get_by_id(db: Session, session_id: int) -> AttendanceSession | None:
    return (
        db.query(AttendanceSession)
        .options(*_EAGER)
        .filter(AttendanceSession.id == session_id)
        .first()
    )


def find_overlapping(
    db: Session, *, section_id: int, session_date: date, start_time: time, end_time: time
) -> AttendanceSession | None:
    return (
        db.query(AttendanceSession)
        .filter(
            AttendanceSession.section_id == section_id,
            AttendanceSession.session_date == session_date,
            AttendanceSession.start_time < end_time,
            AttendanceSession.end_time > start_time,
        )
        .first()
    )


def _apply_filters(query, *, faculty_id, section_id, subject_id, from_date, to_date):
    filters = {"faculty_id": faculty_id, "section_id": section_id, "subject_id": subject_id}
    for attr, value in filters.items():
        if value is not None:
            query = query.filter(getattr(AttendanceSession, attr) == value)
    if from_date is not None:
        query = query.filter(AttendanceSession.session_date >= from_date)
    if to_date is not None:
        query = query.filter(AttendanceSession.session_date <= to_date)
    return query


def list_all(
    db: Session,
    *,
    faculty_id: int | None = None,
    section_id: int | None = None,
    subject_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[AttendanceSession]:
    """Unpaginated — for aggregate counts (e.g. SPEC 12's faculty activity
    report), where every matching session must be counted, not just one
    page of them."""
    query = _apply_filters(
        db.query(AttendanceSession),
        faculty_id=faculty_id,
        section_id=section_id,
        subject_id=subject_id,
        from_date=from_date,
        to_date=to_date,
    )
    return query.all()


def list_paginated(
    db: Session,
    *,
    page: int,
    page_size: int,
    faculty_id: int | None = None,
    section_id: int | None = None,
    subject_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> tuple[list[AttendanceSession], int]:
    query = _apply_filters(
        db.query(AttendanceSession).options(*_EAGER),
        faculty_id=faculty_id,
        section_id=section_id,
        subject_id=subject_id,
        from_date=from_date,
        to_date=to_date,
    )

    total = query.count()
    items = (
        query.order_by(AttendanceSession.session_date.desc(), AttendanceSession.start_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def create(db: Session, session: AttendanceSession) -> AttendanceSession:
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
