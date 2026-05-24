import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, validates

from server.config.constants import MAX_SECTION_DESCRIPTION_LENGTH
from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base


class Sections(
    IDMixin,
    TimestampsMixin,
    Base,
):
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "courses.id",
            ondelete="CASCADE",
        ),
    )
    name: Mapped[str] = mapped_column(
        String(
            255,
        ),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    order_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(
            String,
        ),
    )

    __table_args__ = (
        CheckConstraint(
            f"length(description) <= {MAX_SECTION_DESCRIPTION_LENGTH}",
            name="description_length_check",
        ),
        Index(
            "idx_sections_tags_gin",
            "tags",
            postgresql_using="gin",
        ),
    )

    @validates(
        "description",
    )
    def validate_description_length(
            self,
            key,
            value,
    ):
        if value is not None and (length := len(
                value,
        )) > MAX_SECTION_DESCRIPTION_LENGTH:
            raise ValueError(
                f"The length of the section description should not exceed "
                f"{MAX_SECTION_DESCRIPTION_LENGTH} (actual length: {length}).",
            )
        return value
