import enum

from sqlalchemy import String
from sqlalchemy import Enum as PGEnum
from sqlalchemy.orm import Mapped, mapped_column

from server.database.mixins.id_mixins import IDMixin
from server.database.mixins.timestamp_mixins import TimestampsMixin
from server.database.models.base import Base


class Role(enum.Enum):
    ADMIN = "admin"
    PROFESSOR = "professor"
    STUDENT = "student"


class Users(IDMixin, TimestampsMixin, Base):
    nickname: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), unique=False, nullable=False)
    role: Mapped[Role] = mapped_column(PGEnum(Role, native_enum=True), unique=False, nullable=False)