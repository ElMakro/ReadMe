from typing import Literal
from uuid import UUID

from fastapi import Depends, UploadFile

from server.app.api.v1.auth.auth_manager import AuthManager
from server.app.api.v1.courses.course_state import CourseState
from server.app.api.v1.courses.courses import (
    CourseFullListResponse,
    CourseIDMixin,
    CourseResponse,
    CourseSearchResponse,
    CoursesListSearchResponse,
)
from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.courses.search_strategies import SEARCH_STRATEGIES
from server.app.api.v1.exceptions import (
    BadRequestError,
    ConflictError,
    MediaTypeError,
    ObjectMissingError,
    OperationPermissionError,
)
from server.app.api.v1.users.users import UserVerification
from server.app.api.v1.users.users_manager import UsersManager
from server.app.api.v1.users.users_service import UsersService
from server.data.courses_resources.courses_resources_manager import CoursesResourcesManager
from server.enums.access_permissions import AccessPermissions
from server.enums.role import Role


class CoursesService:
    def __init__(
            self,
            courses_manager: CoursesManager = Depends(
                CoursesManager,
            ),
            auth_manager: AuthManager = Depends(
                AuthManager,
            ),
            users_manager: UsersManager = Depends(
                UsersManager,
            ),
            users_service: UsersService = Depends(
                UsersService,
            ),
            courses_resources_manager: CoursesResourcesManager = Depends(
                CoursesResourcesManager,
            ),
    ) -> None:
        self.courses_resources_manager = courses_resources_manager
        self.users_service = users_service
        self.courses_manager = courses_manager
        self.auth_manager = auth_manager
        self.users_manager = users_manager

    async def get_courses_for_user(
            self,
            user: UserVerification,
            page: int,
            size: int,
    ) -> CourseFullListResponse:
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
    ) -> CourseFullListResponse:
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
            tags: list[str],
    ) -> CourseIDMixin:
        if user.role == Role.STUDENT:
            raise OperationPermissionError(
                "Обучающийся не имеет права на создание курса!",
            )

        if not is_public and is_content_public:
            raise ConflictError(
                "Содержимое курса не может быть публичным, если сам курс непубличный!",
            )

        course = await self.courses_manager.create_course(
            name=name,
            description=description,
            professor_id=user.id,
            is_public=is_public,
            is_content_public=is_content_public,
            tags=tags,
        )

        self.courses_resources_manager.create_course_directory(
            course.id,
        )

        return course

    async def get_course_by_id(
            self,
            user: UserVerification | None,
            course_id: UUID,
    ) -> CourseResponse:
        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if await self.users_service.check_course_access(
                user,
                course=course,
        ) < AccessPermissions.HEADER_ACCESS:
            raise OperationPermissionError(
                "Пользователь не имеет доступа к данному курсу!",
            )

        return course

    async def update_course(
            self,
            user: UserVerification,
            course_id: UUID,
            new_name: str | None,
            new_description: str | None,
            new_is_public: bool | None,
            new_is_content_public: bool | None,
            new_tags: list[str] | None,
    ) -> None:
        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if await self.users_service.check_course_access(
                user,
                course=course,
        ) < AccessPermissions.EDIT_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет прав на изменение курса!",
            )

        if (new_name is None and new_description is None and new_is_public is None
                and new_is_content_public is None and new_tags is None):
            return

        result_name = new_name if new_name is not None else course.name
        result_description = new_description if new_description is not None else course.description
        result_is_public = new_is_public if new_is_public is not None else course.is_public
        result_is_content_public = new_is_content_public if (new_is_content_public
                                                             is not None) else course.is_content_public
        result_tags = new_tags if new_tags is not None else course.tags

        if not result_is_public and result_is_content_public:
            raise ConflictError(
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
            result_tags,
        )

    async def delete_course(
            self,
            user: UserVerification,
            course_id: UUID,
    ):
        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if await self.users_service.check_course_access(
                user,
                course=course,
        ) < AccessPermissions.EDIT_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет прав на удаление курса!",
            )

        await self.courses_manager.delete_course(
            course_id,
        )

        self.courses_resources_manager.delete_course_directory(
            course_id,
        )

    async def resolve_course_state(
            self,
            user_id: UUID | None,
            course: CourseResponse,
    ) -> CourseState | None:
        if user_id is None:
            return CourseState.ENROLLABLE if course.is_public else None

        if user_id == course.professor_id:
            return CourseState.CONTROLLED

        assert user_id is not None

        if await self.courses_manager.check_is_user_enrolled_on_course(
                user_id,
                course.id,
        ):
            return CourseState.ENROLLED

        if course.is_public:
            return CourseState.ENROLLABLE

        return None

    async def search_courses(
            self,
            user: UserVerification | None,
            criteria: Literal["name_prefix", "tag"],
            value: str,
            page: int,
            records_per_page: int,
    ) -> CoursesListSearchResponse:

        strategy = SEARCH_STRATEGIES.get(criteria)
        if strategy is None:
            raise BadRequestError(f"Неподдерживаемый критерий: {criteria}")

        searched_courses = await strategy.search(self.courses_manager, value)

        stated_courses = []

        for course in searched_courses.root:
            state = await self.resolve_course_state(
                user.id if user else None,
                course,
            )

            search_course = course.model_dump()
            search_course["state"] = state

            if state is not None:
                stated_courses.append(
                    CourseSearchResponse.model_validate(
                        search_course,
                    ),
                )

        start = (page - 1) * records_per_page
        end = start + records_per_page
        paginated_courses = stated_courses[start:end]

        return CoursesListSearchResponse.model_validate(
            paginated_courses,
        )

    async def change_course_professor(
            self,
            user: UserVerification,
            course_id: UUID,
            new_professor_id: UUID,
    ) -> None:
        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if await self.users_service.check_course_access(
                user,
                course=course,
        ) < AccessPermissions.EDIT_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет прав на передачу владения курсом!",
            )

        new_professor = await self.users_manager.get_user_by_id(
            new_professor_id,
        )

        if new_professor is None:
            raise ObjectMissingError(
                "Не найден пользователь с идентификатором нового преподавателя!",
            )

        if new_professor.role != Role.PROFESSOR:
            raise OperationPermissionError(
                "У нового преподавателя нет права на ведение курса!",
            )

        await self.courses_manager.change_course_professor(
            course_id,
            new_professor_id,
        )

    async def set_course_icon(
            self,
            user: UserVerification,
            course_id: UUID,
            icon_upload_file: UploadFile,
    ) -> None:
        if "image" not in icon_upload_file.content_type:
            raise MediaTypeError(
                "Некорректный тип файла!",
            )

        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if await self.users_service.check_course_access(
                user,
                course=course,
        ) < AccessPermissions.EDIT_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет прав на установку иконки курса!",
            )

        try:
            await self.courses_resources_manager.set_course_icon(
                course_id,
                icon_upload_file,
            )
        except ValueError as error:
            raise BadRequestError(str(error))

    async def get_course_icon_path(
            self,
            user: UserVerification | None,
            course_id: UUID,
    ):
        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if await self.users_service.check_course_access(
                user,
                course=course,
        ) < AccessPermissions.HEADER_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет прав на просмотр иконки курса!",
            )

        return self.courses_resources_manager.get_course_icon_path(
            course_id,
        )
