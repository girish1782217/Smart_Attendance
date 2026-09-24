from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.user import User


class Faculty(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "faculty"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"), nullable=False, index=True
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    user: Mapped["User"] = relationship("User")
    department: Mapped["Department"] = relationship("Department")
