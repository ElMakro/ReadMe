import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, validates

from server.config.constants import MAX_COURSE_DESCRIPTION_LENGTH
from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base


class Courses(IDMixin, TimestampsMixin, Base):
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    professor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint(
            f"length(description) <= {MAX_COURSE_DESCRIPTION_LENGTH}",
            name="description_length_check"
        ),
    )

    @validates("description")
    def validate_description_length(self, key, value):
        if value is not None and (length := len(value)) > MAX_COURSE_DESCRIPTION_LENGTH:
            raise ValueError(f"The length of the course description should not exceed {MAX_COURSE_DESCRIPTION_LENGTH} "
                             f"(actual length: {length}).")
        return value
