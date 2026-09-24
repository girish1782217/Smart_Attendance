from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.subject import Subject
from app.repositories.master_data_repository import department_crud, subject_crud

SEARCH_FIELDS = ("name", "code")


def _get_department_or_404(db: Session, department_id: int):
    department = department_crud.get_by_id(db, department_id)
    if department is None:
        raise NotFoundError("Department not found.", code="DEPARTMENT_NOT_FOUND")
    return department


def _check_unique(db: Session, *, code: str, exclude_id: int | None = None) -> None:
    query = db.query(Subject).filter(Subject.code == code)
    if exclude_id is not None:
        query = query.filter(Subject.id != exclude_id)
    if query.first() is not None:
        raise ConflictError("A subject with this code already exists.", code="SUBJECT_DUPLICATE_CODE")


def create_subject(
    db: Session, *, name: str, code: str, department_id: int, credits: int | None
) -> Subject:
    _get_department_or_404(db, department_id)
    _check_unique(db, code=code)
    return subject_crud.create(
        db, Subject(name=name, code=code, department_id=department_id, credits=credits)
    )


def get_subject(db: Session, subject_id: int) -> Subject:
    subject = subject_crud.get_by_id(db, subject_id)
    if subject is None:
        raise NotFoundError("Subject not found.", code="SUBJECT_NOT_FOUND")
    return subject


def list_subjects(
    db: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    department_id: int | None = None,
):
    return subject_crud.list_paginated(
        db,
        page=page,
        page_size=page_size,
        search=search,
        search_fields=SEARCH_FIELDS,
        filters={"department_id": department_id},
    )


def update_subject(
    db: Session,
    subject_id: int,
    *,
    name: str | None = None,
    code: str | None = None,
    credits: int | None = None,
    is_active: bool | None = None,
) -> Subject:
    subject = get_subject(db, subject_id)
    if code is not None:
        _check_unique(db, code=code, exclude_id=subject.id)
    return subject_crud.update(
        db, subject, {"name": name, "code": code, "credits": credits, "is_active": is_active}
    )


def deactivate_subject(db: Session, subject_id: int) -> Subject:
    subject = get_subject(db, subject_id)
    return subject_crud.soft_delete(db, subject)
