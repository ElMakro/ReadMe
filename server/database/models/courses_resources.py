import uuid

from sqlalchemy import UUID, String
from sqlalchemy import Enum as PGEnum
from sqlalchemy.orm import Mapped, mapped_column

from server.database.models import Base
from server.enums.object_type import ObjectType


class CoursesResources(
    Base,
):
    __tablename__ = "courses_resources"

    resource_filename: Mapped[str] = mapped_column(
        String(
            512,
        ),
        primary_key=True,
        nullable=False,
    )
    parent_object_id: Mapped[uuid.UUID] = mapped_column(
        UUID(
            as_uuid=True,
        ),
        nullable=False,
        unique=False,
    )
    parent_object_type: Mapped[ObjectType] = mapped_column(
        PGEnum(
            ObjectType,
            native_enum=True,
        ),
        unique=False,
        nullable=False,
    )
