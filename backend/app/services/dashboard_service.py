from datetime import date

from sqlalchemy.orm import Session

from app.models.attendance_session import AttendanceSessionStatus
from app.models.correction_request import CorrectionRequestStatus
from app.repositories import attendance_session_repository, correction_repository, dashboard_repository
from app.services import attendance_history_service, low_attendance_service, settings_service
from app.services.attendance_calculations import calculate_percentage_from_counts


def get_admin_dashboard(db: Session) -> dict:
    today = date.today()
    today_sessions = attendance_session_repository.list_all(db, from_date=today, to_date=today)
    today_submitted = sum(1 for s in today_sessions if s.status == AttendanceSessionStatus.SUBMITTED)

    present_equivalent, total_applicable = dashboard_repository.get_global_attendance_counts(db)
    overall_percentage = calculate_percentage_from_counts(present_equivalent, total_applicable)

    below_threshold_rows, _threshold = low_attendance_service.get_overall_full(
        db, department_id=None, class_id=None, section_id=None, search=None, threshold=None
    )

    _pending_items, pending_total = correction_repository.list_paginated(
        db, page=1, page_size=1, status=CorrectionRequestStatus.PENDING
    )

    return {
        "total_students": dashboard_repository.count_active_students(db),
        "total_faculty": dashboard_repository.count_active_faculty(db),
        "total_departments": dashboard_repository.count_active_departments(db),
        "total_classes": dashboard_repository.count_active_classes(db),
        "today_sessions_total": len(today_sessions),
        "today_sessions_submitted": today_submitted,
        "overall_attendance_percentage": overall_percentage,
        "students_below_threshold": len(below_threshold_rows),
        "pending_correction_requests": pending_total,
    }


def get_faculty_dashboard(db: Session, *, faculty_id: int) -> dict:
    today = date.today()
    today_sessions = attendance_session_repository.list_all(
        db, faculty_id=faculty_id, from_date=today, to_date=today
    )
    all_sessions = attendance_session_repository.list_all(db, faculty_id=faculty_id)

    below_threshold_rows, _threshold = low_attendance_service.get_overall_full(
        db,
        department_id=None,
        class_id=None,
        section_id=None,
        search=None,
        threshold=None,
        faculty_id=faculty_id,
    )

    _pending_items, pending_total = correction_repository.list_paginated(
        db, page=1, page_size=1, status=CorrectionRequestStatus.PENDING, faculty_id=faculty_id
    )

    return {
        "assigned_sections": dashboard_repository.count_distinct_assigned_sections(db, faculty_id),
        "today_sessions": len(today_sessions),
        "total_sessions": len(all_sessions),
        "students_below_threshold": len(below_threshold_rows),
        "pending_correction_requests": pending_total,
    }


def get_student_dashboard(db: Session, *, student_id: int) -> dict:
    summary = attendance_history_service.get_summary(db, student_id=student_id, faculty_id=None)
    records, corrections_by_record_id, _total = attendance_history_service.get_history(
        db,
        student_id=student_id,
        subject_id=None,
        faculty_id=None,
        from_date=None,
        to_date=None,
        page=1,
        page_size=5,
    )
    threshold = settings_service.get_low_attendance_threshold(db)
    overall_percentage = summary["overall"]["percentage"]
    is_low_attendance = overall_percentage is not None and overall_percentage < threshold

    _pending_items, pending_total = correction_repository.list_paginated(
        db, page=1, page_size=1, status=CorrectionRequestStatus.PENDING, student_id=student_id
    )

    return {
        "overall": summary["overall"],
        "by_subject": summary["by_subject"],
        "recent_records": records,
        "recent_corrections_by_record_id": corrections_by_record_id,
        "is_low_attendance": is_low_attendance,
        "threshold": threshold,
        "pending_correction_requests": pending_total,
    }
