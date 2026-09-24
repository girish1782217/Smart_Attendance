from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.models.attendance_record import AttendanceRecord, AttendanceStatus
from app.services.attendance_calculations import calculate_attendance_percentage
from app.services.student_service import get_student  # 404s if missing
from app.repositories import attendance_history_repository, correction_repository


def _counts(statuses: list[AttendanceStatus]) -> dict:
    return {
        "present_count": sum(1 for status in statuses if status == AttendanceStatus.PRESENT),
        "absent_count": sum(1 for status in statuses if status == AttendanceStatus.ABSENT),
        "late_count": sum(1 for status in statuses if status == AttendanceStatus.LATE),
        "excused_count": sum(1 for status in statuses if status == AttendanceStatus.EXCUSED),
        "percentage": calculate_attendance_percentage(statuses),
    }


def get_summary(db: Session, *, student_id: int, faculty_id: int | None) -> dict:
    get_student(db, student_id)  # 404 if the student doesn't exist at all

    records = attendance_history_repository.list_all_for_summary(
        db, student_id=student_id, faculty_id=faculty_id
    )

    overall_statuses = [record.status for record in records]
    by_subject_statuses: dict[int, list[AttendanceStatus]] = defaultdict(list)
    subject_info: dict[int, tuple[str, str]] = {}
    for record in records:
        subject = record.session.subject
        by_subject_statuses[subject.id].append(record.status)
        subject_info[subject.id] = (subject.name, subject.code)

    by_subject = [
        {
            "subject_id": subject_id,
            "subject_name": subject_info[subject_id][0],
            "subject_code": subject_info[subject_id][1],
            **_counts(statuses),
        }
        for subject_id, statuses in sorted(by_subject_statuses.items())
    ]

    return {
        "student_id": student_id,
        "overall": _counts(overall_statuses),
        "by_subject": by_subject,
    }


def get_history(
    db: Session,
    *,
    student_id: int,
    subject_id: int | None,
    faculty_id: int | None,
    from_date: date | None,
    to_date: date | None,
    page: int,
    page_size: int,
) -> tuple[list[AttendanceRecord], dict[int, object], int]:
    get_student(db, student_id)

    records, total = attendance_history_repository.list_paginated(
        db,
        student_id=student_id,
        subject_id=subject_id,
        faculty_id=faculty_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )

    record_ids = [record.id for record in records]
    approved_corrections = correction_repository.list_approved_for_records(db, record_ids)
    corrections_by_record_id = {
        correction.attendance_record_id: correction for correction in approved_corrections
    }

    return records, corrections_by_record_id, total
