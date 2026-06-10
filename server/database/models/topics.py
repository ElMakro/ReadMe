import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import ForeignKey, Index, Integer, String, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_json import mutable_json_type

from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base


class PathType(TypeDecorator):
    impl = String(255)
    cache_ok = True

    def process_bind_param(self, value: Path | str | None, dialect: Any) -> str | None:
        if value is None:
            return None
        return str(value) if isinstance(value, Path) else value

    def process_result_value(self, value: str | None, dialect: Any) -> Path | None:
        if value is None:
            return None
        return Path(value)

    @property
    def python_type(self) -> type[Path]:
        return Path


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
        default=list,
        nullable=False,
    )
    raw_content: Mapped[list[dict[str, str]]] = mapped_column(
        mutable_json_type(
            dbtype=JSONB,
            nested=True,
        ),
        default=list,
        nullable=False,
    )
    rendered_content: Mapped[list[dict[str, str]]] = mapped_column(
        mutable_json_type(
            dbtype=JSONB,
            nested=True,
        ),
        default=list,
        nullable=False,
    )
    topic_directory_path: Mapped[Path] = mapped_column(
        PathType,
        nullable=False,
        unique=True,
    )

    __table_args__ = (
        Index(
            "idx_topics_tags_gin",
            "tags",
            postgresql_using="gin",
        ),
    )
