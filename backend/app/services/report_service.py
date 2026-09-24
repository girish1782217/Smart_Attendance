from datetime import date

from sqlalchemy.orm import Session

from app.models.attendance_session import AttendanceSessionStatus
from app.repositories import attendance_session_repository, low_attendance_repository
from app.services.low_attendance_service import row_to_dict


def get_student_attendance_report(
    db: Session,
    *,
    department_id: int | None,
    class_id: int | None,
    section_id: int | None,
    student_id: int | None,
    search: str | None,
    from_date: date | None,
    to_date: date | None,
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[list[dict], int]:
    """Every student matching the filters (no threshold cutoff — that's
    SPEC 11's job), sorted by roll number. `page`/`page_size` omitted means
    "return everything" (used by the CSV export variant)."""
    rows = low_attendance_repository.aggregate_overall(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        student_id=student_id,
        search=search,
        from_date=from_date,
        to_date=to_date,
    )
    items = sorted((row_to_dict(row) for row in rows), key=lambda item: item["roll_number"])
    total = len(items)
    if page is not None and page_size is not None:
        start = (page - 1) * page_size
        items = items[start : start + page_size]
    return items, total


def get_subject_attendance_report(
    db: Session,
    *,
    department_id: int | None,
    class_id: int | None,
    section_id: int | None,
    subject_id: int | None,
    student_id: int | None,
    search: str | None,
    from_date: date | None,
    to_date: date | None,
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[list[dict], int]:
    rows = low_attendance_repository.aggregate_by_subject(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        student_id=student_id,
        search=search,
        from_date=from_date,
        to_date=to_date,
    )
    items = sorted(
        (row_to_dict(row) for row in rows), key=lambda item: (item["roll_number"], item["subject_code"])
    )
    total = len(items)
    if page is not None and page_size is not None:
        start = (page - 1) * page_size
        items = items[start : start + page_size]
    return items, total


def get_faculty_activity_report(
    db: Session, *, faculty_id: int, from_date: date | None, to_date: date | None
) -> dict:
    all_sessions = attendance_session_repository.list_all(
        db, faculty_id=faculty_id, from_date=from_date, to_date=to_date
    )
    submitted = sum(1 for session in all_sessions if session.status == AttendanceSessionStatus.SUBMITTED)
    scheduled = sum(1 for session in all_sessions if session.status == AttendanceSessionStatus.SCHEDULED)
    return {
        "faculty_id": faculty_id,
        "total_sessions": len(all_sessions),
        "submitted_sessions": submitted,
        "scheduled_sessions": scheduled,
        "from_date": from_date,
        "to_date": to_date,
    }
