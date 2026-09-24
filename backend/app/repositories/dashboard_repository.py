from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.academic_class import AcademicClass
from app.models.attendance_record import AttendanceRecord, AttendanceStatus
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.faculty_assignment import FacultyAssignment
from app.models.student import Student

_PRESENT_EQUIVALENT = case(
    (AttendanceRecord.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE]), 1), else_=0
)
_APPLICABLE = case((AttendanceRecord.status != AttendanceStatus.EXCUSED, 1), else_=0)


def count_active_students(db: Session) -> int:
    return db.query(Student).filter(Student.is_active.is_(True)).count()


def count_active_faculty(db: Session) -> int:
    return db.query(Faculty).filter(Faculty.is_active.is_(True)).count()


def count_active_departments(db: Session) -> int:
    return db.query(Department).filter(Department.is_active.is_(True)).count()


def count_active_classes(db: Session) -> int:
    return db.query(AcademicClass).filter(AcademicClass.is_active.is_(True)).count()


def get_global_attendance_counts(db: Session) -> tuple[int, int]:
    """(present_equivalent, total_applicable) across every attendance
    record ever recorded — the Admin dashboard's college-wide percentage."""
    present_equivalent, total_applicable = db.query(
        func.sum(_PRESENT_EQUIVALENT), func.sum(_APPLICABLE)
    ).one()
    return present_equivalent or 0, total_applicable or 0


def count_distinct_assigned_sections(db: Session, faculty_id: int) -> int:
    return (
        db.query(FacultyAssignment.section_id)
        .filter(FacultyAssignment.faculty_id == faculty_id, FacultyAssignment.is_active.is_(True))
        .distinct()
        .count()
    )
