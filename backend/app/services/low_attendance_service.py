from sqlalchemy.orm import Session

from app.repositories import low_attendance_repository
from app.services import settings_service
from app.services.attendance_calculations import calculate_percentage_from_counts


def row_to_dict(row) -> dict:
    return {
        **row._mapping,
        "percentage": calculate_percentage_from_counts(row.present_equivalent, row.total_applicable),
    }


def get_overall_full(
    db: Session,
    *,
    department_id: int | None,
    class_id: int | None,
    section_id: int | None,
    search: str | None,
    threshold: float | None,
    faculty_id: int | None = None,
) -> tuple[list[dict], float]:
    """The complete (unpaginated) below-threshold list, sorted ascending by
    percentage. Shared by the paginated JSON endpoint, its CSV export
    variant (SPEC 12), and the faculty dashboard's own-sessions-only view
    (SPEC 14, via `faculty_id`) — export must never be silently limited to
    one page."""
    effective_threshold = (
        threshold if threshold is not None else settings_service.get_low_attendance_threshold(db)
    )

    rows = low_attendance_repository.aggregate_overall(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        faculty_id=faculty_id,
        search=search,
    )
    below_threshold = [
        row_to_dict(row)
        for row in rows
        if (pct := calculate_percentage_from_counts(row.present_equivalent, row.total_applicable))
        is not None
        and pct < effective_threshold
    ]
    below_threshold.sort(key=lambda item: item["percentage"])
    return below_threshold, effective_threshold


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
    full, effective_threshold = get_overall_full(
        db, department_id=department_id, class_id=class_id, section_id=section_id, search=search, threshold=threshold
    )
    total = len(full)
    start = (page - 1) * page_size
    return full[start : start + page_size], total, effective_threshold


def get_by_subject_full(
    db: Session,
    *,
    department_id: int | None,
    class_id: int | None,
    section_id: int | None,
    subject_id: int | None,
    search: str | None,
    threshold: float | None,
    faculty_id: int | None = None,
) -> tuple[list[dict], float]:
    effective_threshold = (
        threshold if threshold is not None else settings_service.get_low_attendance_threshold(db)
    )

    rows = low_attendance_repository.aggregate_by_subject(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        faculty_id=faculty_id,
        search=search,
    )
    below_threshold = [
        row_to_dict(row)
        for row in rows
        if (pct := calculate_percentage_from_counts(row.present_equivalent, row.total_applicable))
        is not None
        and pct < effective_threshold
    ]
    below_threshold.sort(key=lambda item: item["percentage"])
    return below_threshold, effective_threshold


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
    full, effective_threshold = get_by_subject_full(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        search=search,
        threshold=threshold,
    )
    total = len(full)
    start = (page - 1) * page_size
    return full[start : start + page_size], total, effective_threshold
