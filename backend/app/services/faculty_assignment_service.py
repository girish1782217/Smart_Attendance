from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.faculty_assignment import FacultyAssignment
from app.repositories import faculty_assignment_repository, faculty_repository
from app.repositories.master_data_repository import section_crud, semester_crud, subject_crud


def create_assignment(
    db: Session, *, faculty_id: int, subject_id: int, section_id: int, semester_id: int
) -> FacultyAssignment:
    if faculty_repository.get_by_id(db, faculty_id) is None:
        raise NotFoundError("Faculty not found.", code="FACULTY_NOT_FOUND")
    if subject_crud.get_by_id(db, subject_id) is None:
        raise NotFoundError("Subject not found.", code="SUBJECT_NOT_FOUND")
    if section_crud.get_by_id(db, section_id) is None:
        raise NotFoundError("Section not found.", code="SECTION_NOT_FOUND")
    if semester_crud.get_by_id(db, semester_id) is None:
        raise NotFoundError("Semester not found.", code="SEMESTER_NOT_FOUND")

    duplicate = faculty_assignment_repository.get_active_duplicate(
        db, faculty_id=faculty_id, subject_id=subject_id, section_id=section_id, semester_id=semester_id
    )
    if duplicate is not None:
        raise ConflictError("This faculty assignment already exists.", code="ASSIGNMENT_DUPLICATE")

    assignment = FacultyAssignment(
        faculty_id=faculty_id, subject_id=subject_id, section_id=section_id, semester_id=semester_id
    )
    return faculty_assignment_repository.create(db, assignment)


def get_assignment(db: Session, assignment_id: int) -> FacultyAssignment:
    assignment = faculty_assignment_repository.get_by_id(db, assignment_id)
    if assignment is None:
        raise NotFoundError("Faculty assignment not found.", code="ASSIGNMENT_NOT_FOUND")
    return assignment


def list_assignments(
    db: Session,
    *,
    page: int,
    page_size: int,
    faculty_id: int | None = None,
    subject_id: int | None = None,
    section_id: int | None = None,
    semester_id: int | None = None,
) -> tuple[list[FacultyAssignment], int]:
    return faculty_assignment_repository.list_paginated(
        db,
        page=page,
        page_size=page_size,
        faculty_id=faculty_id,
        subject_id=subject_id,
        section_id=section_id,
        semester_id=semester_id,
    )


def deactivate_assignment(db: Session, assignment_id: int) -> FacultyAssignment:
    assignment = get_assignment(db, assignment_id)
    return faculty_assignment_repository.deactivate(db, assignment)
