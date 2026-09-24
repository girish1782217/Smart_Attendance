from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.academic_class import AcademicClass
from app.repositories.master_data_repository import class_crud, program_crud

SEARCH_FIELDS = ("name",)


def _get_program_or_404(db: Session, program_id: int):
    program = program_crud.get_by_id(db, program_id)
    if program is None:
        raise NotFoundError("Program not found.", code="PROGRAM_NOT_FOUND")
    return program


def _check_unique(db: Session, *, program_id: int, name: str, exclude_id: int | None = None) -> None:
    query = db.query(AcademicClass).filter(
        AcademicClass.program_id == program_id, AcademicClass.name == name
    )
    if exclude_id is not None:
        query = query.filter(AcademicClass.id != exclude_id)
    if query.first() is not None:
        raise ConflictError(
            "A class with this name already exists in this program.", code="CLASS_DUPLICATE"
        )


def create_class(db: Session, *, name: str, program_id: int) -> AcademicClass:
    _get_program_or_404(db, program_id)
    _check_unique(db, program_id=program_id, name=name)
    return class_crud.create(db, AcademicClass(name=name, program_id=program_id))


def get_class(db: Session, class_id: int) -> AcademicClass:
    academic_class = class_crud.get_by_id(db, class_id)
    if academic_class is None:
        raise NotFoundError("Class not found.", code="CLASS_NOT_FOUND")
    return academic_class


def list_classes(
    db: Session, *, page: int, page_size: int, search: str | None = None, program_id: int | None = None
):
    return class_crud.list_paginated(
        db,
        page=page,
        page_size=page_size,
        search=search,
        search_fields=SEARCH_FIELDS,
        filters={"program_id": program_id},
    )


def update_class(
    db: Session, class_id: int, *, name: str | None = None, is_active: bool | None = None
) -> AcademicClass:
    academic_class = get_class(db, class_id)
    if name is not None:
        _check_unique(db, program_id=academic_class.program_id, name=name, exclude_id=academic_class.id)
    return class_crud.update(db, academic_class, {"name": name, "is_active": is_active})


def deactivate_class(db: Session, class_id: int) -> AcademicClass:
    academic_class = get_class(db, class_id)
    return class_crud.soft_delete(db, academic_class)
