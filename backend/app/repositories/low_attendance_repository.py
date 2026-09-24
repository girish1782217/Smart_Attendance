from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.models.academic_class import AcademicClass
from app.models.attendance_record import AttendanceRecord, AttendanceStatus
from app.models.attendance_session import AttendanceSession
from app.models.program import Program
from app.models.section import Section
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User

_PRESENT = case((AttendanceRecord.status == AttendanceStatus.PRESENT, 1), else_=0)
_ABSENT = case((AttendanceRecord.status == AttendanceStatus.ABSENT, 1), else_=0)
_LATE = case((AttendanceRecord.status == AttendanceStatus.LATE, 1), else_=0)
_EXCUSED = case((AttendanceRecord.status == AttendanceStatus.EXCUSED, 1), else_=0)
_PRESENT_EQUIVALENT = case(
    (AttendanceRecord.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE]), 1), else_=0
)
_APPLICABLE = case((AttendanceRecord.status != AttendanceStatus.EXCUSED, 1), else_=0)

_COUNT_COLUMNS = (
    func.sum(_PRESENT).label("present_count"),
    func.sum(_ABSENT).label("absent_count"),
    func.sum(_LATE).label("late_count"),
    func.sum(_EXCUSED).label("excused_count"),
    func.sum(_PRESENT_EQUIVALENT).label("present_equivalent"),
    func.sum(_APPLICABLE).label("total_applicable"),
)


def _apply_common_filters(
    query, *, department_id: int | None, class_id: int | None, section_id: int | None, search: str | None
):
    if department_id is not None:
        query = query.filter(Program.department_id == department_id)
    if class_id is not None:
        query = query.filter(AcademicClass.id == class_id)
    if section_id is not None:
        query = query.filter(Student.section_id == section_id)
    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(Student.roll_number.ilike(like_pattern), User.full_name.ilike(like_pattern))
        )
    return query


def aggregate_overall(
    db: Session,
    *,
    department_id: int | None = None,
    class_id: int | None = None,
    section_id: int | None = None,
    search: str | None = None,
):
    """One row per student with any attendance record, aggregated across
    all their subjects. The INNER JOIN to attendance_records naturally
    excludes students with zero records — see the "no attendance data"
    design note in docs/sdd/11-low-attendance-spec.md."""
    query = (
        db.query(
            Student.id.label("student_id"),
            Student.roll_number.label("roll_number"),
            User.full_name.label("student_name"),
            *_COUNT_COLUMNS,
        )
        .join(AttendanceRecord, AttendanceRecord.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .join(Section, Student.section_id == Section.id)
        .join(AcademicClass, Section.class_id == AcademicClass.id)
        .join(Program, AcademicClass.program_id == Program.id)
        .filter(Student.is_active.is_(True))
    )
    query = _apply_common_filters(
        query, department_id=department_id, class_id=class_id, section_id=section_id, search=search
    )
    return query.group_by(Student.id, Student.roll_number, User.full_name).all()


def aggregate_by_subject(
    db: Session,
    *,
    department_id: int | None = None,
    class_id: int | None = None,
    section_id: int | None = None,
    subject_id: int | None = None,
    search: str | None = None,
):
    """One row per (student, subject) with any attendance record for that
    subject."""
    query = (
        db.query(
            Student.id.label("student_id"),
            Student.roll_number.label("roll_number"),
            User.full_name.label("student_name"),
            Subject.id.label("subject_id"),
            Subject.name.label("subject_name"),
            Subject.code.label("subject_code"),
            *_COUNT_COLUMNS,
        )
        .join(AttendanceRecord, AttendanceRecord.student_id == Student.id)
        .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)
        .join(Subject, AttendanceSession.subject_id == Subject.id)
        .join(User, Student.user_id == User.id)
        .join(Section, Student.section_id == Section.id)
        .join(AcademicClass, Section.class_id == AcademicClass.id)
        .join(Program, AcademicClass.program_id == Program.id)
        .filter(Student.is_active.is_(True))
    )
    query = _apply_common_filters(
        query, department_id=department_id, class_id=class_id, section_id=section_id, search=search
    )
    if subject_id is not None:
        query = query.filter(Subject.id == subject_id)

    return query.group_by(
        Student.id, Student.roll_number, User.full_name, Subject.id, Subject.name, Subject.code
    ).all()
