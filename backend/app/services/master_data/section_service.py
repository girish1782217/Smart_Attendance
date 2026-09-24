from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.section import Section
from app.repositories.master_data_repository import class_crud, section_crud

SEARCH_FIELDS = ("name",)


def _get_class_or_404(db: Session, class_id: int):
    academic_class = class_crud.get_by_id(db, class_id)
    if academic_class is None:
        raise NotFoundError("Class not found.", code="CLASS_NOT_FOUND")
    return academic_class


def _check_unique(db: Session, *, class_id: int, name: str, exclude_id: int | None = None) -> None:
    query = db.query(Section).filter(Section.class_id == class_id, Section.name == name)
    if exclude_id is not None:
        query = query.filter(Section.id != exclude_id)
    if query.first() is not None:
        raise ConflictError(
            "A section with this name already exists in this class.", code="SECTION_DUPLICATE"
        )


def create_section(db: Session, *, name: str, class_id: int, capacity: int | None) -> Section:
    _get_class_or_404(db, class_id)
    _check_unique(db, class_id=class_id, name=name)
    return section_crud.create(db, Section(name=name, class_id=class_id, capacity=capacity))


def get_section(db: Session, section_id: int) -> Section:
    section = section_crud.get_by_id(db, section_id)
    if section is None:
        raise NotFoundError("Section not found.", code="SECTION_NOT_FOUND")
    return section


def list_sections(
    db: Session, *, page: int, page_size: int, search: str | None = None, class_id: int | None = None
):
    return section_crud.list_paginated(
        db,
        page=page,
        page_size=page_size,
        search=search,
        search_fields=SEARCH_FIELDS,
        filters={"class_id": class_id},
    )


def update_section(
    db: Session,
    section_id: int,
    *,
    name: str | None = None,
    capacity: int | None = None,
    is_active: bool | None = None,
) -> Section:
    section = get_section(db, section_id)
    if name is not None:
        _check_unique(db, class_id=section.class_id, name=name, exclude_id=section.id)
    return section_crud.update(db, section, {"name": name, "capacity": capacity, "is_active": is_active})


def deactivate_section(db: Session, section_id: int) -> Section:
    section = get_section(db, section_id)
    return section_crud.soft_delete(db, section)
