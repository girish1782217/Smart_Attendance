from sqlalchemy.orm import Session, joinedload

from app.models.attendance_record import AttendanceRecord
from app.models.student import Student


def get_by_id(db: Session, record_id: int) -> AttendanceRecord | None:
    return (
        db.query(AttendanceRecord)
        .options(
            joinedload(AttendanceRecord.student).joinedload(Student.user),
            joinedload(AttendanceRecord.session),
        )
        .filter(AttendanceRecord.id == record_id)
        .first()
    )


def list_by_session(db: Session, session_id: int) -> list[AttendanceRecord]:
    return (
        db.query(AttendanceRecord)
        .options(joinedload(AttendanceRecord.student).joinedload(Student.user))
        .filter(AttendanceRecord.session_id == session_id)
        .all()
    )


def list_by_student(db: Session, student_id: int) -> list[AttendanceRecord]:
    return db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student_id).all()
