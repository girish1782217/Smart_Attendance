from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.faculty import Faculty
    from app.models.section import Section
    from app.models.semester import Semester
    from app.models.subject import Subject


class FacultyAssignment(Base, TimestampMixin, SoftDeleteMixin):
    """Says "this faculty member teaches this subject to this section in
    this semester". SPEC 07's attendance sessions are validated against
    active rows here (a faculty member may only record a session for a
    (section, subject) pair they're assigned to).

    Uniqueness is enforced only among *active* rows (a partial index, not a
    blanket UniqueConstraint) — deactivating an assignment and later
    recreating the identical (faculty, subject, section, semester)
    combination is a legitimate, expected flow (e.g. undoing a mistaken
    deactivation, or a faculty rotation reverting next semester... within
    the same semester row this also just means "re-enable"), and a
    non-partial constraint would block it even though the app-level
    duplicate check (which only looks at is_active=True rows) allows it.
    """

    __tablename__ = "faculty_assignments"
    __table_args__ = (
        Index(
            "uq_faculty_assignment_active",
            "faculty_id",
            "subject_id",
            "section_id",
            "semester_id",
            unique=True,
            sqlite_where=text("is_active = 1"),
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id"), nullable=False, index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False, index=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False, index=True)

    faculty: Mapped["Faculty"] = relationship("Faculty")
    subject: Mapped["Subject"] = relationship("Subject")
    section: Mapped["Section"] = relationship("Section")
    semester: Mapped["Semester"] = relationship("Semester")
