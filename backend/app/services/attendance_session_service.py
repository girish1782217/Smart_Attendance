from datetime import date, time

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.attendance_session import AttendanceSession, AttendanceSessionStatus
from app.models.student import Student
from app.repositories import (
    attendance_session_repository,
    faculty_assignment_repository,
    faculty_repository,
    student_repository,
)
from app.repositories.master_data_repository import section_crud, subject_crud


def create_session(
    db: Session,
    *,
    faculty_id: int,
    subject_id: int,
    section_id: int,
    session_date: date,
    start_time: time,
    end_time: time,
) -> AttendanceSession:
    if faculty_repository.get_by_id(db, faculty_id) is None:
        raise NotFoundError("Faculty not found.", code="FACULTY_NOT_FOUND")
    if subject_crud.get_by_id(db, subject_id) is None:
        raise NotFoundError("Subject not found.", code="SUBJECT_NOT_FOUND")
    if section_crud.get_by_id(db, section_id) is None:
        raise NotFoundError("Section not found.", code="SECTION_NOT_FOUND")

    assignment = faculty_assignment_repository.get_active_for_faculty_subject_section(
        db, faculty_id=faculty_id, subject_id=subject_id, section_id=section_id
    )
    if assignment is None:
        raise ForbiddenError(
            "This faculty member is not assigned to teach this subject for this section.",
            code="FACULTY_NOT_ASSIGNED",
        )

    overlapping = attendance_session_repository.find_overlapping(
        db, section_id=section_id, session_date=session_date, start_time=start_time, end_time=end_time
    )
    if overlapping is not None:
        raise ConflictError(
            "This section already has an overlapping session on this date.",
            code="SESSION_TIME_OVERLAP",
        )

    session = AttendanceSession(
        faculty_id=faculty_id,
        subject_id=subject_id,
        section_id=section_id,
        session_date=session_date,
        start_time=start_time,
        end_time=end_time,
        status=AttendanceSessionStatus.SCHEDULED,
    )
    return attendance_session_repository.create(db, session)


def get_session(db: Session, session_id: int) -> AttendanceSession:
    session = attendance_session_repository.get_by_id(db, session_id)
    if session is None:
        raise NotFoundError("Attendance session not found.", code="ATTENDANCE_SESSION_NOT_FOUND")
    return session


def list_sessions(
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
    return attendance_session_repository.list_paginated(
        db,
        page=page,
        page_size=page_size,
        faculty_id=faculty_id,
        section_id=section_id,
        subject_id=subject_id,
        from_date=from_date,
        to_date=to_date,
    )


def get_roster(db: Session, session_id: int) -> list[Student]:
    session = get_session(db, session_id)
    return student_repository.list_active_by_section(db, section_id=session.section_id)


def ensure_faculty_can_access(effective_faculty_id: int | None, session: AttendanceSession) -> None:
    """effective_faculty_id is None for ADMIN (unrestricted); for any other
    caller it's their own resolved id — enforce it matches the session's
    owner."""
    if effective_faculty_id is not None and session.faculty_id != effective_faculty_id:
        raise ForbiddenError(
            "You do not have access to this attendance session.", code="FORBIDDEN"
        )
