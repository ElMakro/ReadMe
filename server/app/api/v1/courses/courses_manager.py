import uuid
from uuid import UUID

from fastapi import Depends
from sqlalchemy import delete, select

from server.app.api.v1.courses.courses import CourseFullListResponse, CourseIDMixin, CourseResponse, CoursesList
from server.config.db_dependency import DBDependency
from server.database.models import Courses, CoursesForStudents


class ObjectExistenceError(
    ValueError,
):
    """Исключение, связанное с отсутствием объекта"""
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

    async def get_controlled_courses(
            self,
            user_id: uuid.UUID,
            offset: int,
            limit: int,
    ) -> CoursesList:
        async with self.db.db_session() as session:
            query = select(
                self.courses_model,
            ).where(
                self.courses_model.professor_id == user_id,
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

            courses = result.scalars().all()
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
            tags: list[str],
    ) -> CourseIDMixin:
        async with self.db.db_session() as session:
            course = Courses(
                name=name,
                description=description,
                professor_id=professor_id,
                is_public=is_public,
                is_content_public=is_content_public,
                tags=tags,
            )

            session.add(
                course,
            )
            await session.commit()

        return CourseIDMixin.model_validate(
            course,
        )

    async def get_course_by_id(
            self,
            course_id: UUID,
    ) -> CourseResponse:
        async with self.db.db_session() as session:
            course = await session.get(
                Courses,
                course_id,
            )

        if course is None:
            raise ObjectExistenceError(
                "Курса с таким ID не существует!",
            )

        return CourseResponse.model_validate(
            course,
        )

    async def check_is_user_enrolled_on_course(
            self,
            user_id: UUID,
            course_id: UUID,
    ) -> bool:
        async with self.db.db_session() as session:
            query = select(
                self.courses_for_students_model,
            ).where(
                self.courses_for_students_model.student_id == user_id,
                self.courses_for_students_model.course_id == course_id,
            )
            result = await session.execute(
                query,
            )
            record = result.one_or_none()

        return bool(
            record,
        )

    async def self_enroll_on_course(
            self,
            user_id: UUID,
            course_id: UUID,
    ) -> None:
        async with self.db.db_session() as session:
            record = CoursesForStudents(
                student_id=user_id,
                course_id=course_id,
            )
            session.add(
                record,
            )
            await session.commit()

    async def self_unenroll_from_course(
            self,
            user_id: UUID,
            course_id: UUID,
    ) -> None:
        await self.get_course_by_id(
            course_id,
        )

        async with self.db.db_session() as session:
            query = delete(
                self.courses_for_students_model,
            ).where(
                self.courses_for_students_model.student_id == user_id,
                self.courses_for_students_model.course_id == course_id,
            )

            await session.execute(
                query,
            )
            await session.commit()

    async def update_course(
            self,
            course_id: UUID,
            name: str,
            description: str,
            is_public: bool,
            is_content_public: bool,
            tags: list[str],
    ) -> None:
        async with self.db.db_session() as session:
            course = await session.get(
                Courses,
                course_id,
                with_for_update=True,
            )

            course.name = name
            course.description = description
            course.is_public = is_public
            course.is_content_public = is_content_public
            course.tags = tags

            await session.commit()

    async def delete_course(
            self,
            course_id: UUID,
    ) -> None:
        async with self.db.db_session() as session:
            course = await session.get(
                Courses,
                course_id,
                with_for_update=True,
            )

            await session.delete(
                course,
            )
            await session.commit()

    async def search_courses_by_name_prefix(
            self,
            course_name_prefix: str,
    ) -> CourseFullListResponse:
        async with self.db.db_session() as session:
            query = select(
                self.courses_model,
            ).where(
                self.courses_model.name.ilike(
                    f"{course_name_prefix}%",
                ),
            )
            result = await session.execute(
                query,
            )

            courses = result.scalars().all()

            return CourseFullListResponse.model_validate(
                courses,
            )

    async def change_course_professor(
            self,
            course_id: UUID,
            new_professor_id: UUID,
    ) -> None:
        async with self.db.db_session() as session:
            course = await session.get(
                Courses,
                course_id,
                with_for_update=True,
            )

            course.professor_id = new_professor_id

            await session.commit()

    async def search_courses_by_tag(
            self,
            tag: str,
    ) -> CourseFullListResponse:
        async with self.db.db_session() as session:
            query = select(
                Courses,
            ).where(
                Courses.tags.contains(
                    [tag],
                ),
            )
            result = await session.execute(
                query,
            )

            courses = result.scalars().all()

        return CourseFullListResponse.model_validate(
            courses,
        )
