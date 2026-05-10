import uuid

from fastapi import Depends
from sqlalchemy import select

from server.config.db_dependency import DBDependency
from server.database.models import Courses, CoursesForStudents
from server.schemas.courses import CoursesList


class CoursesManager:
    def __init__(self, db: DBDependency = Depends(DBDependency)) -> None:
        self.db = db
        self.courses_model = Courses
        self.courses_for_students_model = CoursesForStudents

    async def get_courses_of_user(self, user_id: uuid.UUID) -> CoursesList:
        async with self.db.db_session() as session:
            query = select(
                self.courses_model.name, self.courses_model.description
                           ).join(
                self.courses_for_students_model, self.courses_model.id == self.courses_for_students_model.course_id
            ).where(self.courses_for_students_model.student_id == user_id)
            result = await session.execute(query)
            courses = result.mappings().all()
            return CoursesList.model_validate(courses)
