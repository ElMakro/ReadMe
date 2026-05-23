import uuid

from sqlalchemy import Enum as PGEnum
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base
from server.enums.application_status import ApplicationStatus


class ProfessorsApplications(IDMixin, TimestampsMixin, Base):
    __tablename__ = "professors_applications"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    surname: Mapped[str] = mapped_column(String(32), nullable=False)
    patronymic: Mapped[str] = mapped_column(String(32), nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        PGEnum(ApplicationStatus, native_enum=True),
        unique=False,
        nullable=False,
        default=ApplicationStatus.PENDING,
    )

    __table_args__ = (
        Index("idx_status_created", "status", "created_at"),
    )
