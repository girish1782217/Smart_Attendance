from sqlalchemy.orm import Session, joinedload

from app.models.faculty_assignment import FacultyAssignment


def get_by_id(db: Session, assignment_id: int) -> FacultyAssignment | None:
    return db.get(FacultyAssignment, assignment_id)


def get_active_duplicate(
    db: Session, *, faculty_id: int, subject_id: int, section_id: int, semester_id: int
) -> FacultyAssignment | None:
    return (
        db.query(FacultyAssignment)
        .filter(
            FacultyAssignment.faculty_id == faculty_id,
            FacultyAssignment.subject_id == subject_id,
            FacultyAssignment.section_id == section_id,
            FacultyAssignment.semester_id == semester_id,
            FacultyAssignment.is_active.is_(True),
        )
        .first()
    )


def list_paginated(
    db: Session,
    *,
    page: int,
    page_size: int,
    faculty_id: int | None = None,
    subject_id: int | None = None,
    section_id: int | None = None,
    semester_id: int | None = None,
) -> tuple[list[FacultyAssignment], int]:
    query = db.query(FacultyAssignment).options(
        joinedload(FacultyAssignment.faculty),
        joinedload(FacultyAssignment.subject),
        joinedload(FacultyAssignment.section),
        joinedload(FacultyAssignment.semester),
    )

    filters = {
        "faculty_id": faculty_id,
        "subject_id": subject_id,
        "section_id": section_id,
        "semester_id": semester_id,
    }
    for attr, value in filters.items():
        if value is not None:
            query = query.filter(getattr(FacultyAssignment, attr) == value)

    total = query.count()
    items = (
        query.order_by(FacultyAssignment.id).offset((page - 1) * page_size).limit(page_size).all()
    )
    return items, total


def create(db: Session, assignment: FacultyAssignment) -> FacultyAssignment:
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def deactivate(db: Session, assignment: FacultyAssignment) -> FacultyAssignment:
    assignment.is_active = False
    db.commit()
    db.refresh(assignment)
    return assignment
