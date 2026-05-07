import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from server.database.models.base import Base


class CoursesForStudents(Base):
    __tablename__ = "courses_for_students"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course")
    )
