from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.student import Student
from app.models.user import User


def get_by_id(db: Session, student_id: int) -> Student | None:
    return db.query(Student).options(joinedload(Student.user)).filter(Student.id == student_id).first()


def get_by_roll_number(db: Session, roll_number: str) -> Student | None:
    return db.query(Student).filter(Student.roll_number == roll_number).first()


def get_by_user_id(db: Session, user_id: int) -> Student | None:
    return db.query(Student).filter(Student.user_id == user_id).first()


def list_active_by_section(db: Session, *, section_id: int) -> list[Student]:
    return (
        db.query(Student)
        .options(joinedload(Student.user))
        .filter(Student.section_id == section_id, Student.is_active.is_(True))
        .order_by(Student.roll_number)
        .all()
    )


def list_paginated(
    db: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    section_id: int | None = None,
) -> tuple[list[Student], int]:
    query = db.query(Student).join(User, Student.user_id == User.id).options(joinedload(Student.user))

    if section_id is not None:
        query = query.filter(Student.section_id == section_id)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Student.roll_number.ilike(like_pattern),
                User.full_name.ilike(like_pattern),
                User.email.ilike(like_pattern),
            )
        )

    total = query.count()
    items = query.order_by(Student.id).offset((page - 1) * page_size).limit(page_size).all()
    return items, total
