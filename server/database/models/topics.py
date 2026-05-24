import uuid

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base


class Topics(
    IDMixin,
    TimestampsMixin,
    Base,
):
    section_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "sections.id",
            ondelete="CASCADE",
        ),
    )
    name: Mapped[str] = mapped_column(
        String(
            255,
        ),
        nullable=False,
    )
    order_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "courses.id",
            ondelete="CASCADE",
        ),
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(
            String,
        ),
    )

    __table_args__ = (
        Index(
            "idx_topics_tags_gin",
            "tags",
            postgresql_using="gin",
        ),
    )
