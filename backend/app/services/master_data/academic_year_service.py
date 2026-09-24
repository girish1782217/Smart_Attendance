from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.academic_year import AcademicYear
from app.repositories.master_data_repository import academic_year_crud

SEARCH_FIELDS = ("name",)


def _check_unique(db: Session, *, name: str, exclude_id: int | None = None) -> None:
    query = db.query(AcademicYear).filter(AcademicYear.name == name)
    if exclude_id is not None:
        query = query.filter(AcademicYear.id != exclude_id)
    if query.first() is not None:
        raise ConflictError(
            "An academic year with this name already exists.", code="ACADEMIC_YEAR_DUPLICATE"
        )


def create_academic_year(db: Session, *, name: str, start_date: date, end_date: date) -> AcademicYear:
    _check_unique(db, name=name)
    return academic_year_crud.create(db, AcademicYear(name=name, start_date=start_date, end_date=end_date))


def get_academic_year(db: Session, academic_year_id: int) -> AcademicYear:
    year = academic_year_crud.get_by_id(db, academic_year_id)
    if year is None:
        raise NotFoundError("Academic year not found.", code="ACADEMIC_YEAR_NOT_FOUND")
    return year


def list_academic_years(db: Session, *, page: int, page_size: int, search: str | None = None):
    return academic_year_crud.list_paginated(
        db, page=page, page_size=page_size, search=search, search_fields=SEARCH_FIELDS
    )


def update_academic_year(
    db: Session,
    academic_year_id: int,
    *,
    name: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    is_active: bool | None = None,
) -> AcademicYear:
    year = get_academic_year(db, academic_year_id)
    if name is not None:
        _check_unique(db, name=name, exclude_id=year.id)

    effective_start = start_date if start_date is not None else year.start_date
    effective_end = end_date if end_date is not None else year.end_date
    if effective_end <= effective_start:
        raise ValidationAppError("end_date must be after start_date.", code="INVALID_DATE_RANGE")

    return academic_year_crud.update(
        db, year, {"name": name, "start_date": start_date, "end_date": end_date, "is_active": is_active}
    )


def deactivate_academic_year(db: Session, academic_year_id: int) -> AcademicYear:
    year = get_academic_year(db, academic_year_id)
    return academic_year_crud.soft_delete(db, year)
