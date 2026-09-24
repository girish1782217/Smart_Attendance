from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.program import Program
    from app.models.section import Section


class AcademicClass(Base, TimestampMixin, SoftDeleteMixin):
    """A year/level within a Program, e.g. "First Year" under "B.Tech CSE".

    Named `AcademicClass` (table `classes`) to avoid colliding with the
    Python `class` keyword — the API-facing term is still "class"
    (`/api/v1/classes`).
    """

    __tablename__ = "classes"
    __table_args__ = (UniqueConstraint("program_id", "name", name="uq_class_program_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), nullable=False, index=True)

    program: Mapped["Program"] = relationship("Program", back_populates="classes")
    sections: Mapped[list["Section"]] = relationship("Section", back_populates="academic_class")
