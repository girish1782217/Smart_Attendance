from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.roles import RoleName
from app.core.security import hash_password
from app.models.student import Student
from app.models.user import User
from app.repositories import role_repository, student_repository, user_repository
from app.repositories.master_data_repository import section_crud


def create_student(
    db: Session,
    *,
    email: str,
    full_name: str,
    password: str,
    roll_number: str,
    section_id: int,
    phone: str | None = None,
) -> Student:
    if user_repository.get_by_email(db, email) is not None:
        raise ConflictError("A user with this email already exists.", code="USER_EMAIL_EXISTS")
    if student_repository.get_by_roll_number(db, roll_number) is not None:
        raise ConflictError(
            "A student with this roll number already exists.", code="STUDENT_ROLL_NUMBER_DUPLICATE"
        )
    if section_crud.get_by_id(db, section_id) is None:
        raise NotFoundError("Section not found.", code="SECTION_NOT_FOUND")

    student_role = role_repository.get_by_name(db, RoleName.STUDENT.value)
    user = User(email=email, full_name=full_name, hashed_password=hash_password(password), is_active=True)
    user.roles = [student_role]
    db.add(user)
    db.flush()  # assign user.id without committing, so a later failure rolls both back together

    student = Student(user_id=user.id, roll_number=roll_number, section_id=section_id, phone=phone)
    db.add(student)
    db.commit()
    db.refresh(student)
    db.refresh(user)
    return student


def get_student(db: Session, student_id: int) -> Student:
    student = student_repository.get_by_id(db, student_id)
    if student is None:
        raise NotFoundError("Student not found.", code="STUDENT_NOT_FOUND")
    return student


def list_students(
    db: Session, *, page: int, page_size: int, search: str | None = None, section_id: int | None = None
) -> tuple[list[Student], int]:
    return student_repository.list_paginated(
        db, page=page, page_size=page_size, search=search, section_id=section_id
    )


def update_student(
    db: Session,
    student_id: int,
    *,
    full_name: str | None = None,
    phone: str | None = None,
    section_id: int | None = None,
    is_active: bool | None = None,
) -> Student:
    student = get_student(db, student_id)

    if section_id is not None:
        if section_crud.get_by_id(db, section_id) is None:
            raise NotFoundError("Section not found.", code="SECTION_NOT_FOUND")
        student.section_id = section_id

    if phone is not None:
        student.phone = phone
    if is_active is not None:
        student.is_active = is_active
    if full_name is not None:
        student.user.full_name = full_name

    db.commit()
    db.refresh(student)
    return student


def deactivate_student(db: Session, student_id: int) -> Student:
    student = get_student(db, student_id)
    student.is_active = False
    student.user.is_active = False
    db.commit()
    db.refresh(student)
    return student
