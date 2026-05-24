from uuid import UUID

from fastapi import Depends

from server.app.api.v1.courses.courses import CourseResponse
from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.users.enums.access_permissions import AccessPermissions
from server.app.api.v1.users.users import (
    ApplicationChangeStatus,
    ApplicationsList,
    ApplicationsUserList,
    ProfessorApplication,
    UserProfile,
    UsersList,
    UserVerification,
    UserWithRole,
)
from server.app.api.v1.users.users_manager import UsersManager
from server.enums.role import Role


class UsersService:
    def __init__(
            self,
            users_manager: UsersManager = Depends(
                UsersManager,
            ),
            courses_manager: CoursesManager = Depends(
                CoursesManager,
            ),
    ) -> None:
        self.users_manager = users_manager
        self.courses_manager = courses_manager

    def get_info_for_user_profile(
            self,
            user: UserVerification,
    ) -> UserProfile:
        return UserProfile(
            id=user.id,
            nickname=user.nickname,
            email=user.email,
            role=user.role,
        )

    async def check_course_access(
            self,
            user: UserVerification | None,
            course_id: UUID | None = None,
            course: CourseResponse | None = None,
    ) -> AccessPermissions:
        if user is not None:
            if user.role == Role.ADMIN:
                return AccessPermissions.EDIT_ACCESS

        if course is None:
            if course_id is None:
                raise ValueError(
                    "Либо курс, либо его идентификатор должны быть переданы!",
                )
            else:
                course = await self.courses_manager.get_course_by_id(
                    course_id,
                )

        if course_id is None:
            course_id = course.id

        if user is not None:
            if course.professor_id == user.id:
                return AccessPermissions.EDIT_ACCESS

        if course.is_content_public:
            return AccessPermissions.CONTENT_ACCESS

        if course.is_public:
            return AccessPermissions.HEADER_ACCESS

        if user is not None:
            if await self.courses_manager.check_is_user_enrolled_on_course(
                    user.id,
                    course_id,
            ):
                return AccessPermissions.CONTENT_ACCESS

        return AccessPermissions.NO_ACCESS

    async def get_all_users(self, page: int, size: int) -> UsersList:
        offset = (page - 1) * size
        limit = size
        return await self.users_manager.get_all_users(
            offset,
            limit,
        )

    async def change_role(self, user: UserWithRole) -> None:
        return await self.users_manager.change_role(id=user.id, role=user.role)

    async def delete_user(self, id: UUID) -> None:
        return await self.users_manager.delete_user(id=id)

    async def reg_professor_application(self, id: UUID, application: ProfessorApplication) -> None:
        return await self.users_manager.reg_professor_application(
            id=id,
            name=application.name,
            surname=application.surname,
            patronymic=application.patronymic,
        )

    async def get_professor_applications(self, page: int, size: int) -> ApplicationsList:
        offset = (page - 1) * size
        limit = size
        return await self.users_manager.get_professor_applications(
            offset,
            limit,
        )

    async def change_application_status(self, application: ApplicationChangeStatus) -> None:
        return await self.users_manager.change_application_status(
            id=application.application_id,
            user_id=application.user_id,
            status=application.status,
            comment=application.admin_comment,
        )

    async def get_user_applications(self, id: UUID, page: int, size: int) -> ApplicationsUserList:
        offset = (page - 1) * size
        limit = size
        return await self.users_manager.get_user_applications(id=id, offset=offset, limit=limit)
