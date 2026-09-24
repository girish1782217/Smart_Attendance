from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.faculty import Faculty
from app.models.user import User


def get_by_id(db: Session, faculty_id: int) -> Faculty | None:
    return db.query(Faculty).options(joinedload(Faculty.user)).filter(Faculty.id == faculty_id).first()


def get_by_employee_id(db: Session, employee_id: str) -> Faculty | None:
    return db.query(Faculty).filter(Faculty.employee_id == employee_id).first()


def get_by_user_id(db: Session, user_id: int) -> Faculty | None:
    return db.query(Faculty).filter(Faculty.user_id == user_id).first()


def list_paginated(
    db: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    department_id: int | None = None,
) -> tuple[list[Faculty], int]:
    query = db.query(Faculty).join(User, Faculty.user_id == User.id).options(joinedload(Faculty.user))

    if department_id is not None:
        query = query.filter(Faculty.department_id == department_id)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Faculty.employee_id.ilike(like_pattern),
                User.full_name.ilike(like_pattern),
                User.email.ilike(like_pattern),
            )
        )

    total = query.count()
    items = query.order_by(Faculty.id).offset((page - 1) * page_size).limit(page_size).all()
    return items, total
