from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.department import Department
from app.repositories.master_data_repository import department_crud

SEARCH_FIELDS = ("name", "code")


def _check_unique(db: Session, *, name: str, code: str, exclude_id: int | None = None) -> None:
    query = db.query(Department).filter((Department.name == name) | (Department.code == code))
    if exclude_id is not None:
        query = query.filter(Department.id != exclude_id)
    existing = query.first()
    if existing is not None:
        field = "name" if existing.name == name else "code"
        raise ConflictError(
            f"A department with this {field} already exists.", code="DEPARTMENT_DUPLICATE"
        )


def create_department(db: Session, *, name: str, code: str) -> Department:
    _check_unique(db, name=name, code=code)
    return department_crud.create(db, Department(name=name, code=code))


def get_department(db: Session, department_id: int) -> Department:
    department = department_crud.get_by_id(db, department_id)
    if department is None:
        raise NotFoundError("Department not found.", code="DEPARTMENT_NOT_FOUND")
    return department


def list_departments(db: Session, *, page: int, page_size: int, search: str | None = None):
    return department_crud.list_paginated(
        db, page=page, page_size=page_size, search=search, search_fields=SEARCH_FIELDS
    )


def update_department(
    db: Session,
    department_id: int,
    *,
    name: str | None = None,
    code: str | None = None,
    is_active: bool | None = None,
) -> Department:
    department = get_department(db, department_id)
    if name is not None or code is not None:
        _check_unique(
            db, name=name or department.name, code=code or department.code, exclude_id=department.id
        )
    return department_crud.update(db, department, {"name": name, "code": code, "is_active": is_active})


def deactivate_department(db: Session, department_id: int) -> Department:
    department = get_department(db, department_id)
    return department_crud.soft_delete(db, department)
