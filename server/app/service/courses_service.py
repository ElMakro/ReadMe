from uuid import UUID

from fastapi import Depends

from server.app.service.auth_handler import AuthHandler
from server.app.service.courses_manager import CoursesManager
from server.enums.role import Role
from server.schemas.courses import CourseIDMixin, CourseResponse, CoursesList
from server.schemas.users import UserVerification


class CourseOperationPermissionError(
    ValueError,
):
    """Исключение, связанное с наличием у пользователя прав на операцию над курсом"""
    pass


class CoursePrivacyLevelsError(
    ValueError,
):
    """Исключение, связанное с противоречием в уровнях доступности курсов"""
    pass


class UserEnrollmentError(
    ValueError,
):
    """Исключение, связанное с записью пользователя на курс"""
    pass


class CoursesService:
    def __init__(
            self,
            manager: CoursesManager = Depends(
                CoursesManager,
            ),
            auth_handler: AuthHandler = Depends(
                AuthHandler,
            ),
    ) -> None:
        self.courses_manager = manager
        self.auth_handler = auth_handler

    async def get_courses_for_user(
            self,
            user: UserVerification,
            page: int,
            size: int,
    ) -> CoursesList:
        offset = (page - 1) * size
        limit = size
        return await self.courses_manager.get_courses_of_user(
            user.id,
            offset,
            limit,
        )

    async def get_controlled_courses(
            self,
            user: UserVerification,
            page: int,
            records_per_page: int,
    ) -> CoursesList:
        offset = (page - 1) * records_per_page
        return await self.courses_manager.get_controlled_courses(
            user.id,
            offset,
            records_per_page,
        )

    async def create_course(
            self,
            user: UserVerification,
            name: str,
            description: str,
            is_public: bool,
            is_content_public: bool,
    ) -> CourseIDMixin:
        if user.role == Role.STUDENT:
            raise CourseOperationPermissionError(
                "Обучающийся не имеет права на создание курса!",
            )

        if not is_public and is_content_public:
            raise CoursePrivacyLevelsError(
                "Содержимое курса не может быть публичным, если сам курс непубличный!",
            )

        return await self.courses_manager.create_course(
            name=name,
            description=description,
            professor_id=user.id,
            is_public=is_public,
            is_content_public=is_content_public,
        )

    async def get_course_by_id(
            self,
            user: UserVerification,
            course_id: UUID,
    ) -> CourseResponse:
        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if course.is_public:
            return course

        if course.professor_id == user.id:
            return course

        if await self.courses_manager.check_is_user_enrolled_on_course(
                user.id,
                course_id,
        ):
            return course

        raise CourseOperationPermissionError(
            "Пользователь не имеет доступа к данному курсу!",
        )

    async def self_enroll_on_course(
            self,
            user: UserVerification,
            course_id: UUID,
    ) -> None:
        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if course.professor_id == user.id:
            raise UserEnrollmentError(
                "Пользователь является преподавателем на данном курсе!",
            )

        if await self.courses_manager.check_is_user_enrolled_on_course(
                user.id,
                course_id,
        ):
            raise UserEnrollmentError(
                "Пользователь уже записан на данный курс!",
            )

        await self.courses_manager.self_enroll_on_course(
            user.id,
            course_id,
        )

    async def self_unenroll_from_course(
            self,
            user: UserVerification,
            course_id: UUID,
    ) -> None:
        await self.courses_manager.self_unenroll_from_course(
            user.id,
            course_id,
        )

    async def update_course(
            self,
            user: UserVerification,
            course_id: UUID,
            new_name: str | None,
            new_description: str | None,
            new_is_public: bool | None,
            new_is_content_public: bool | None,
    ) -> None:
        if user.role == Role.STUDENT:
            raise CourseOperationPermissionError(
                "Обучающийся не имеет права на редактирование курса!",
            )

        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if user.role == Role.PROFESSOR and course.professor_id != user.id:
            raise CourseOperationPermissionError(
                "Преподаватель может изменить только тот курс, который он ведёт!",
            )

        if new_name is None and new_description is None and new_is_public is None and new_is_content_public is None:
            return

        result_name = new_name if new_name is not None else course.name
        result_description = new_description if new_description is not None else course.description
        result_is_public = new_is_public if new_is_public is not None else course.is_public
        result_is_content_public = new_is_content_public if (new_is_content_public
                                                             is not None) else course.is_content_public

        if not result_is_public and result_is_content_public:
            raise CoursePrivacyLevelsError(
                "Содержимое курса не может быть публичным, если сам курс непубличный!",
            )

        if (course.name == result_name and course.description == result_description and
                course.is_public == result_is_public and course.is_content_public == result_is_content_public):
            return

        await self.courses_manager.update_course(
            course_id,
            result_name,
            result_description,
            result_is_public,
            result_is_content_public,
        )

    async def delete_course(
            self,
            user: UserVerification,
            course_id: UUID,
    ):
        if user.role == Role.STUDENT:
            raise CourseOperationPermissionError(
                "Обучающийся не имеет права на удаление курса!",
            )

        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if user.role == Role.PROFESSOR and course.professor_id != user.id:
            raise CourseOperationPermissionError(
                "Преподаватель может удалить только тот курс, который он ведёт!",
            )

        await self.courses_manager.delete_course(
            course_id,
        )
