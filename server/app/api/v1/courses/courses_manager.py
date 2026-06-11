import uuid
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select

from server.app.api.v1.courses.courses import CourseFullListResponse, CourseIDMixin, CourseResponse
from server.app.api.v1.exceptions import BadRequestError, ObjectMissingError
from server.config.constants import MAX_COURSE_DESCRIPTION_LENGTH
from server.config.db_dependency import DBDependency
from server.database.models import Courses, CoursesForStudents, ProfessorsDetails


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
        self.professors_model = ProfessorsDetails

    async def get_courses_of_user(
            self,
            user_id: uuid.UUID,
            offset: int,
            limit: int,
    ) -> CourseFullListResponse:
        async with self.db.db_session() as session:
            query = select(
                self.courses_model.id,
                self.courses_model.name,
                self.courses_model.description,
                self.courses_model.is_public,
                self.courses_model.is_content_public,
                self.courses_model.tags,
                self.courses_model.created_at,
                self.courses_model.updated_at,
                self.courses_model.professor_id,
                self.professors_model.name.label("professor_name"),
                self.professors_model.surname.label("professor_surname"),
                self.professors_model.patronymic.label("professor_patronymic"),
            ).join(
                self.courses_for_students_model,
                self.courses_model.id == self.courses_for_students_model.course_id,
            ).join(
                self.professors_model,
                self.professors_model.id == self.courses_model.professor_id,
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
            return CourseFullListResponse.model_validate(
                courses,
            )

    async def get_controlled_courses(
            self,
            user_id: uuid.UUID,
            offset: int,
            limit: int,
    ) -> CourseFullListResponse:
        async with self.db.db_session() as session:
            query = select(
                self.courses_model.id,
                self.courses_model.name,
                self.courses_model.description,
                self.courses_model.is_public,
                self.courses_model.is_content_public,
                self.courses_model.tags,
                self.courses_model.created_at,
                self.courses_model.updated_at,
                self.courses_model.professor_id,
                self.professors_model.name.label("professor_name"),
                self.professors_model.surname.label("professor_surname"),
                self.professors_model.patronymic.label("professor_patronymic"),
            ).join(
                self.professors_model,
                self.professors_model.id == self.courses_model.professor_id,
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

            courses = result.mappings().all()
            return CourseFullListResponse.model_validate(
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
            try:
                course = Courses(
                    name=name,
                    description=description,
                    professor_id=professor_id,
                    is_public=is_public,
                    is_content_public=is_content_public,
                    tags=tags,
                )
            except ValueError:
                raise BadRequestError(f"Описание курса не может превышать {MAX_COURSE_DESCRIPTION_LENGTH} символов!")

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
            query = select(
                self.courses_model.id,
                self.courses_model.name,
                self.courses_model.description,
                self.courses_model.is_public,
                self.courses_model.is_content_public,
                self.courses_model.tags,
                self.courses_model.created_at,
                self.courses_model.updated_at,
                self.courses_model.professor_id,
                self.professors_model.name.label("professor_name"),
                self.professors_model.surname.label("professor_surname"),
                self.professors_model.patronymic.label("professor_patronymic"),
            ).join(
                self.professors_model,
                self.professors_model.id == self.courses_model.professor_id,
            ).where(
                self.courses_model.id == course_id
            )
            result = await session.execute(
                query,
            )
            course = result.mappings().one_or_none()

        if course is None:
            raise ObjectMissingError(
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

            try:
                course.description = description
            except ValueError:
                raise BadRequestError(f"Описание курса не может превышать {MAX_COURSE_DESCRIPTION_LENGTH} символов!")

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

            if course is None:
                raise ObjectMissingError("Курса с таким идентификатором не найдено!")

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
                self.courses_model.id,
                self.courses_model.name,
                self.courses_model.description,
                self.courses_model.is_public,
                self.courses_model.is_content_public,
                self.courses_model.tags,
                self.courses_model.created_at,
                self.courses_model.updated_at,
                self.courses_model.professor_id,
                self.professors_model.name.label("professor_name"),
                self.professors_model.surname.label("professor_surname"),
                self.professors_model.patronymic.label("professor_patronymic"),
            ).join(
                self.professors_model,
                self.professors_model.id == self.courses_model.professor_id,
            ).where(
                self.courses_model.name.ilike(
                    f"{course_name_prefix}%",
                ),
            )
            result = await session.execute(
                query,
            )

            courses = result.mappings().all()

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
                self.courses_model.id,
                self.courses_model.name,
                self.courses_model.description,
                self.courses_model.is_public,
                self.courses_model.is_content_public,
                self.courses_model.tags,
                self.courses_model.created_at,
                self.courses_model.updated_at,
                self.courses_model.professor_id,
                self.professors_model.name.label("professor_name"),
                self.professors_model.surname.label("professor_surname"),
                self.professors_model.patronymic.label("professor_patronymic"),
            ).join(
                self.professors_model,
                self.professors_model.id == self.courses_model.professor_id,
            ).where(
                Courses.tags.contains(
                    [tag],
                ),
            )
            result = await session.execute(
                query,
            )

            courses = result.mappings().all()

        return CourseFullListResponse.model_validate(
            courses,
        )
