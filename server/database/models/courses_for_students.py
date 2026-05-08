import uuid

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from server.database.models.base import Base


class CoursesForStudents(Base):
    __tablename__ = "courses_for_students"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))

    __table_args__ = (
        PrimaryKeyConstraint("student_id", "course_id", name="pq_student_course"),
    )
