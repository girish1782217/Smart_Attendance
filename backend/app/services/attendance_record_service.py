from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.attendance_record import AttendanceRecord, AttendanceStatus
from app.models.attendance_session import AttendanceSession, AttendanceSessionStatus
from app.repositories import attendance_record_repository, student_repository
from app.services import attendance_session_service


def bulk_mark(
    db: Session,
    *,
    session_id: int,
    items: list[tuple[int, AttendanceStatus]],
    recorded_by_user_id: int,
) -> list[AttendanceRecord]:
    session = attendance_session_service.get_session(db, session_id)
    if session.status != AttendanceSessionStatus.SCHEDULED:
        raise ConflictError(
            "This session has already been submitted; use a correction request to change a record.",
            code="SESSION_ALREADY_SUBMITTED",
        )

    roster_ids = {
        student.id for student in student_repository.list_active_by_section(db, section_id=session.section_id)
    }
    for student_id, _status in items:
        if student_id not in roster_ids:
            raise NotFoundError(
                f"Student {student_id} is not an active member of this session's section.",
                code="STUDENT_NOT_IN_ROSTER",
            )

    existing_by_student = {
        record.student_id: record for record in attendance_record_repository.list_by_session(db, session_id)
    }

    results: list[AttendanceRecord] = []
    for student_id, status in items:
        existing = existing_by_student.get(student_id)
        if existing is not None:
            existing.status = status
            existing.recorded_by_user_id = recorded_by_user_id
            results.append(existing)
        else:
            new_record = AttendanceRecord(
                session_id=session_id,
                student_id=student_id,
                status=status,
                recorded_by_user_id=recorded_by_user_id,
            )
            db.add(new_record)
            results.append(new_record)

    db.commit()
    for record in results:
        db.refresh(record)
    return results


def list_records(db: Session, session_id: int) -> list[AttendanceRecord]:
    attendance_session_service.get_session(db, session_id)  # 404s if missing
    return attendance_record_repository.list_by_session(db, session_id)


def submit_session(db: Session, session_id: int) -> AttendanceSession:
    session = attendance_session_service.get_session(db, session_id)
    if session.status == AttendanceSessionStatus.SUBMITTED:
        raise ConflictError("This session has already been submitted.", code="SESSION_ALREADY_SUBMITTED")

    roster = student_repository.list_active_by_section(db, section_id=session.section_id)
    recorded_student_ids = {
        record.student_id for record in attendance_record_repository.list_by_session(db, session_id)
    }
    missing = [student for student in roster if student.id not in recorded_student_ids]
    if missing:
        raise ConflictError(
            f"Cannot submit: {len(missing)} student(s) in the roster have no attendance record yet.",
            code="INCOMPLETE_ROSTER",
        )

    session.status = AttendanceSessionStatus.SUBMITTED
    db.commit()
    db.refresh(session)
    return session
