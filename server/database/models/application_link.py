import re

from sqlalchemy import CheckConstraint
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, validates

from server.config.constants import ALLOWED_LINK_CHARACTERS
from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base


class ApplicationLink(IDMixin, TimestampsMixin, Base):
    __tablename__ = "application_link"

    secret_part: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    __table_args__ = (
        CheckConstraint(
            f"secret_part ~ '{ALLOWED_LINK_CHARACTERS}'",
            name="link_characters_check"
        ),
    )

    @validates("secret_part")
    def validate_link_characters(self, key, value):
        if not re.fullmatch(ALLOWED_LINK_CHARACTERS, value):
            raise ValueError(
                f"Ссылка содержит недопустимые символы: разрешены только {ALLOWED_LINK_CHARACTERS}."
            )
        return value
