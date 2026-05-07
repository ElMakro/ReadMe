import uuid

from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base


class Notes(IDMixin, TimestampsMixin, Base):
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
