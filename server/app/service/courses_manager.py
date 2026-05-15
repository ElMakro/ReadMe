import uuid
from uuid import UUID

from fastapi import Depends
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from server.config.db_dependency import DBDependency
from server.database.models import Courses, CoursesForStudents
from server.schemas.courses import CourseIDMixin, CourseResponse, CoursesList
from server.schemas.users import UserVerification


class UserEnrollmentError(
    ValueError,
):
    pass


class CourseAccessPermissionError(
    ValueError,
):
    pass


class CourseExistenceError(
    ValueError,
):
    pass


class CoursesManager:
    def __init__(
            self,
            db: DBDependency = Depends(
                DBDependency,
            ),
    ) -> None:
        self.db = db
        self.courses_model = Courses
        self.courses_for_students_model = CoursesForStudents

    async def get_courses_of_user(
            self,
            user_id: uuid.UUID,
            offset: int,
            limit: int,
    ) -> CoursesList:
        async with self.db.db_session() as session:
            query = select(
                self.courses_model.id,
                self.courses_model.name,
                self.courses_model.description,
            ).join(
                self.courses_for_students_model,
                self.courses_model.id == self.courses_for_students_model.course_id,
            ).where(
                self.courses_for_students_model.student_id == user_id,
            ).order_by(
                self.courses_model.id,
            ).offset(
                offset,
            ).limit(
                limit,
            )
            result = await session.execute(
                query,
            )
            courses = result.mappings().all()
            return CoursesList.model_validate(
                courses,
            )

    async def create_course(
            self,
            name: str,
            description: str,
            professor_id: uuid.UUID,
            is_public: bool,
            is_content_public: bool,
    ) -> CourseIDMixin:
        async with self.db.db_session() as session:
            query = insert(
                self.courses_model,
            ).values(
                name=name,
                description=description,
                professor_id=professor_id,
                is_public=is_public,
                is_content_public=is_content_public,
            ).returning(
                self.courses_model.id,
            )
            result = await session.execute(
                query,
            )
            created_course = result.mappings().one()

            await session.commit()
            return CourseIDMixin.model_validate(
                created_course,
            )

    async def get_course_by_id(
            self,
            user: UserVerification,
            course_id: UUID,
    ) -> CourseResponse:
        async with self.db.db_session() as session:
            query = select(
                self.courses_model,
            ).where(
                self.courses_model.id == course_id,
            )

            result = await session.execute(
                query,
            )
            course = result.scalars().one_or_none()

        if course is None:
            raise CourseExistenceError()

        course = CourseResponse.model_validate(
            course,
        )

        if course.is_public:
            return course

        if course.professor_id == user.id:
            return course

        async with self.db.db_session() as session:
            query = select(
                self.courses_for_students_model,
            ).where(
                self.courses_for_students_model.student_id == user.id,
                self.courses_for_students_model.course_id == course_id,
            )
            result = await session.execute(
                query,
            )
            record = result.one_or_none()

        if record:
            return course

        raise CourseAccessPermissionError()

    async def self_enroll_on_course(
            self,
            user: UserVerification,
            course_id: UUID,
    ) -> None:
        course = await self.get_course_by_id(
            user,
            course_id,
        )

        if course.professor_id == user.id:
            raise UserEnrollmentError(
                "Пользователь является преподавателем на данном курсе",
            )

        async with self.db.db_session() as session:
            query = insert(
                self.courses_for_students_model,
            ).values(
                student_id=user.id,
                course_id=course_id,
            )

            try:
                await session.execute(
                    query,
                )
                await session.commit()
            except IntegrityError:
                raise UserEnrollmentError(
                    "Пользователь уже записан на данный курс",
                )
