from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.program import Program
from app.repositories.master_data_repository import department_crud, program_crud

SEARCH_FIELDS = ("name", "code")


def _get_department_or_404(db: Session, department_id: int):
    department = department_crud.get_by_id(db, department_id)
    if department is None:
        raise NotFoundError("Department not found.", code="DEPARTMENT_NOT_FOUND")
    return department


def _check_unique(
    db: Session, *, department_id: int, name: str, code: str, exclude_id: int | None = None
) -> None:
    name_query = db.query(Program).filter(Program.department_id == department_id, Program.name == name)
    code_query = db.query(Program).filter(Program.code == code)
    if exclude_id is not None:
        name_query = name_query.filter(Program.id != exclude_id)
        code_query = code_query.filter(Program.id != exclude_id)
    if name_query.first() is not None:
        raise ConflictError(
            "A program with this name already exists in this department.",
            code="PROGRAM_DUPLICATE_NAME",
        )
    if code_query.first() is not None:
        raise ConflictError("A program with this code already exists.", code="PROGRAM_DUPLICATE_CODE")


def create_program(db: Session, *, name: str, code: str, department_id: int) -> Program:
    _get_department_or_404(db, department_id)
    _check_unique(db, department_id=department_id, name=name, code=code)
    return program_crud.create(db, Program(name=name, code=code, department_id=department_id))


def get_program(db: Session, program_id: int) -> Program:
    program = program_crud.get_by_id(db, program_id)
    if program is None:
        raise NotFoundError("Program not found.", code="PROGRAM_NOT_FOUND")
    return program


def list_programs(
    db: Session, *, page: int, page_size: int, search: str | None = None, department_id: int | None = None
):
    return program_crud.list_paginated(
        db,
        page=page,
        page_size=page_size,
        search=search,
        search_fields=SEARCH_FIELDS,
        filters={"department_id": department_id},
    )


def update_program(
    db: Session,
    program_id: int,
    *,
    name: str | None = None,
    code: str | None = None,
    is_active: bool | None = None,
) -> Program:
    program = get_program(db, program_id)
    if name is not None or code is not None:
        _check_unique(
            db,
            department_id=program.department_id,
            name=name or program.name,
            code=code or program.code,
            exclude_id=program.id,
        )
    return program_crud.update(db, program, {"name": name, "code": code, "is_active": is_active})


def deactivate_program(db: Session, program_id: int) -> Program:
    program = get_program(db, program_id)
    return program_crud.soft_delete(db, program)
