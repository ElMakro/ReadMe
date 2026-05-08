import uuid

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from server.database.models.base import Base


class AchievementsForStudents(Base):
    __tablename__ = "achievements_for_students"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    achievement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("achievements.id", ondelete="CASCADE"))

    __table_args__ = (
        PrimaryKeyConstraint("student_id", "achievement_id", name="pq_student_achievement"),
    )
