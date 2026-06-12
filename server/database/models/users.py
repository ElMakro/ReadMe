from sqlalchemy import CheckConstraint, String, func
from sqlalchemy import Enum as PGEnum
from sqlalchemy.orm import Mapped, mapped_column, validates

from server.config.constants import MAX_USER_NAME_LENGTH, MIN_USER_NAME_LENGTH
from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base
from server.enums.role import Role


class Users(IDMixin, TimestampsMixin, Base):
    nickname: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), unique=False, nullable=False)
    role: Mapped[Role] = mapped_column(PGEnum(Role, native_enum=True), unique=False, nullable=False)

    __table_args__ = (
        CheckConstraint(
            func.length(nickname).between(MIN_USER_NAME_LENGTH, MAX_USER_NAME_LENGTH),
            name="nickname_length_check"
        ),
    )

    @validates("nickname")
    def validate_nickname_length(self, key, value):
        if not (MIN_USER_NAME_LENGTH <= (length := len(value)) <= MAX_USER_NAME_LENGTH):
            raise ValueError(f"The length of the nickname should be in range from {MIN_USER_NAME_LENGTH}"
                             f"to {MAX_USER_NAME_LENGTH} (actual length: {length}).")
        return value
