from sqlalchemy.orm import Session

from app.repositories import low_attendance_repository
from app.services import settings_service
from app.services.attendance_calculations import calculate_percentage_from_counts


def _row_to_dict(row) -> dict:
    return {
        **row._mapping,
        "percentage": calculate_percentage_from_counts(row.present_equivalent, row.total_applicable),
    }


def get_overall_low_attendance(
    db: Session,
    *,
    department_id: int | None,
    class_id: int | None,
    section_id: int | None,
    search: str | None,
    threshold: float | None,
    page: int,
    page_size: int,
) -> tuple[list[dict], int, float]:
    effective_threshold = threshold if threshold is not None else settings_service.get_low_attendance_threshold(db)

    rows = low_attendance_repository.aggregate_overall(
        db, department_id=department_id, class_id=class_id, section_id=section_id, search=search
    )
    below_threshold = [
        _row_to_dict(row)
        for row in rows
        if (pct := calculate_percentage_from_counts(row.present_equivalent, row.total_applicable))
        is not None
        and pct < effective_threshold
    ]
    below_threshold.sort(key=lambda item: item["percentage"])

    total = len(below_threshold)
    start = (page - 1) * page_size
    page_items = below_threshold[start : start + page_size]
    return page_items, total, effective_threshold


def get_by_subject_low_attendance(
    db: Session,
    *,
    department_id: int | None,
    class_id: int | None,
    section_id: int | None,
    subject_id: int | None,
    search: str | None,
    threshold: float | None,
    page: int,
    page_size: int,
) -> tuple[list[dict], int, float]:
    effective_threshold = threshold if threshold is not None else settings_service.get_low_attendance_threshold(db)

    rows = low_attendance_repository.aggregate_by_subject(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        search=search,
    )
    below_threshold = [
        _row_to_dict(row)
        for row in rows
        if (pct := calculate_percentage_from_counts(row.present_equivalent, row.total_applicable))
        is not None
        and pct < effective_threshold
    ]
    below_threshold.sort(key=lambda item: item["percentage"])

    total = len(below_threshold)
    start = (page - 1) * page_size
    page_items = below_threshold[start : start + page_size]
    return page_items, total, effective_threshold
