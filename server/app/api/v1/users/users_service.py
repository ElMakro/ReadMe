from uuid import UUID

from fastapi import Depends

from server.app.api.v1.courses.courses import CourseResponse
from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.users.enums.access_permissions import AccessPermissions
from server.app.api.v1.users.users import UserProfile, UserVerification
from server.enums.role import Role


class UsersService:
    def __init__(
            self,
            courses_manager: CoursesManager = Depends(
                CoursesManager,
            ),
    ) -> None:
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
