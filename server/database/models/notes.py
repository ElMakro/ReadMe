import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, validates

from server.config.constants import MAX_NOTE_LENGTH
from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base


class Notes(IDMixin, TimestampsMixin, Base):
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            f"length(content) <= {MAX_NOTE_LENGTH}",
            name="length_check"
        ),
    )

    @validates("content")
    def validate_note_length(self, key, value):
        if value is not None and (length := len(value)) > MAX_NOTE_LENGTH:
            raise ValueError(f"The length of the notes should not exceed {MAX_NOTE_LENGTH} (actual length: {length}).")
        return value
