from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.academic_year import AcademicYear
from app.models.semester import Semester
from app.repositories.master_data_repository import academic_year_crud, semester_crud

SEARCH_FIELDS = ("name",)


def _check_unique(
    db: Session, *, academic_year_id: int, name: str, exclude_id: int | None = None
) -> None:
    query = db.query(Semester).filter(
        Semester.academic_year_id == academic_year_id, Semester.name == name
    )
    if exclude_id is not None:
        query = query.filter(Semester.id != exclude_id)
    if query.first() is not None:
        raise ConflictError(
            "A semester with this name already exists in this academic year.",
            code="SEMESTER_DUPLICATE",
        )


def _get_academic_year_or_404(db: Session, academic_year_id: int) -> AcademicYear:
    year = academic_year_crud.get_by_id(db, academic_year_id)
    if year is None:
        raise NotFoundError("Academic year not found.", code="ACADEMIC_YEAR_NOT_FOUND")
    return year


def _validate_within_year(year: AcademicYear, start_date: date, end_date: date) -> None:
    if start_date < year.start_date or end_date > year.end_date:
        raise ValidationAppError(
            "Semester dates must fall within the academic year's date range.",
            code="SEMESTER_OUTSIDE_ACADEMIC_YEAR",
        )


def create_semester(
    db: Session, *, name: str, academic_year_id: int, start_date: date, end_date: date
) -> Semester:
    year = _get_academic_year_or_404(db, academic_year_id)
    _validate_within_year(year, start_date, end_date)
    _check_unique(db, academic_year_id=academic_year_id, name=name)
    return semester_crud.create(
        db,
        Semester(name=name, academic_year_id=academic_year_id, start_date=start_date, end_date=end_date),
    )


def get_semester(db: Session, semester_id: int) -> Semester:
    semester = semester_crud.get_by_id(db, semester_id)
    if semester is None:
        raise NotFoundError("Semester not found.", code="SEMESTER_NOT_FOUND")
    return semester


def list_semesters(
    db: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    academic_year_id: int | None = None,
):
    return semester_crud.list_paginated(
        db,
        page=page,
        page_size=page_size,
        search=search,
        search_fields=SEARCH_FIELDS,
        filters={"academic_year_id": academic_year_id},
    )


def update_semester(
    db: Session,
    semester_id: int,
    *,
    name: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    is_active: bool | None = None,
) -> Semester:
    semester = get_semester(db, semester_id)
    if name is not None:
        _check_unique(
            db, academic_year_id=semester.academic_year_id, name=name, exclude_id=semester.id
        )

    effective_start = start_date if start_date is not None else semester.start_date
    effective_end = end_date if end_date is not None else semester.end_date
    year = _get_academic_year_or_404(db, semester.academic_year_id)
    _validate_within_year(year, effective_start, effective_end)

    return semester_crud.update(
        db, semester, {"name": name, "start_date": start_date, "end_date": end_date, "is_active": is_active}
    )


def deactivate_semester(db: Session, semester_id: int) -> Semester:
    semester = get_semester(db, semester_id)
    return semester_crud.soft_delete(db, semester)
