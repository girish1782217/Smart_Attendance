from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.roles import RoleName
from app.core.security import hash_password
from app.models.faculty import Faculty
from app.models.user import User
from app.repositories import faculty_repository, role_repository, user_repository
from app.repositories.master_data_repository import department_crud


def create_faculty(
    db: Session,
    *,
    email: str,
    full_name: str,
    password: str,
    employee_id: str,
    department_id: int,
    phone: str | None = None,
) -> Faculty:
    if user_repository.get_by_email(db, email) is not None:
        raise ConflictError("A user with this email already exists.", code="USER_EMAIL_EXISTS")
    if faculty_repository.get_by_employee_id(db, employee_id) is not None:
        raise ConflictError(
            "A faculty member with this employee id already exists.",
            code="FACULTY_EMPLOYEE_ID_DUPLICATE",
        )
    if department_crud.get_by_id(db, department_id) is None:
        raise NotFoundError("Department not found.", code="DEPARTMENT_NOT_FOUND")

    faculty_role = role_repository.get_by_name(db, RoleName.FACULTY.value)
    user = User(email=email, full_name=full_name, hashed_password=hash_password(password), is_active=True)
    user.roles = [faculty_role]
    db.add(user)
    db.flush()

    faculty = Faculty(
        user_id=user.id, employee_id=employee_id, department_id=department_id, phone=phone
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    db.refresh(user)
    return faculty


def get_faculty(db: Session, faculty_id: int) -> Faculty:
    faculty = faculty_repository.get_by_id(db, faculty_id)
    if faculty is None:
        raise NotFoundError("Faculty not found.", code="FACULTY_NOT_FOUND")
    return faculty


def list_faculty(
    db: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    department_id: int | None = None,
) -> tuple[list[Faculty], int]:
    return faculty_repository.list_paginated(
        db, page=page, page_size=page_size, search=search, department_id=department_id
    )


def update_faculty(
    db: Session,
    faculty_id: int,
    *,
    full_name: str | None = None,
    phone: str | None = None,
    department_id: int | None = None,
    is_active: bool | None = None,
) -> Faculty:
    faculty = get_faculty(db, faculty_id)

    if department_id is not None:
        if department_crud.get_by_id(db, department_id) is None:
            raise NotFoundError("Department not found.", code="DEPARTMENT_NOT_FOUND")
        faculty.department_id = department_id

    if phone is not None:
        faculty.phone = phone
    if is_active is not None:
        faculty.is_active = is_active
    if full_name is not None:
        faculty.user.full_name = full_name

    db.commit()
    db.refresh(faculty)
    return faculty


def deactivate_faculty(db: Session, faculty_id: int) -> Faculty:
    faculty = get_faculty(db, faculty_id)
    faculty.is_active = False
    faculty.user.is_active = False
    db.commit()
    db.refresh(faculty)
    return faculty
