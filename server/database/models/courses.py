import uuid

from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base


class Courses(IDMixin, TimestampsMixin, Base):
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    professor: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    path_to_directory: Mapped[str] = mapped_column(String(255), nullable=False)
