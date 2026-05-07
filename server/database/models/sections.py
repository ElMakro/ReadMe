import uuid

from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base


class Sections(IDMixin, TimestampsMixin, Base):
    course: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)
