from sqlalchemy import Boolean, CheckConstraint, String, true
from sqlalchemy.orm import Mapped, mapped_column

from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base


class ApplicationLink(IDMixin, TimestampsMixin, Base):
    __tablename__ = "application_link"

    secret_part: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    single: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true(),
        unique=True,
    )

    __table_args__ = (
        CheckConstraint(
            "single IS TRUE",
            name="single_must_be_true",
        ),
    )
