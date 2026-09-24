from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.academic_class import AcademicClass
    from app.models.department import Department


class Program(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "programs"
    __table_args__ = (UniqueConstraint("department_id", "name", name="uq_program_department_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"), nullable=False, index=True
    )

    department: Mapped["Department"] = relationship("Department", back_populates="programs")
    classes: Mapped[list["AcademicClass"]] = relationship("AcademicClass", back_populates="program")
