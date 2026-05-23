import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.database.models.base import Base


class ProfessorsDetails(Base):
    __tablename__ = "professors_details"

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    surname: Mapped[str] = mapped_column(String(32), nullable=False)
    patronymic: Mapped[str] = mapped_column(String(32), nullable=True)

    user_info = relationship("Users")
