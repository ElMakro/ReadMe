from uuid import UUID

from fastapi import Depends, HTTPException, status

from server.app.service.auth_handler import AuthHandler
from server.app.service.courses_manager import CoursesManager
from server.enums.role import Role
from server.schemas.courses import CourseIDMixin, CourseResponse, CoursesList
from server.schemas.users import UserVerification


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

    async def create_course(
            self,
            user: UserVerification,
            name: str,
            description: str,
            is_open: bool,
    ) -> CourseIDMixin:
        if user.role == Role.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return await self.courses_manager.create_course(
            name=name,
            description=description,
            professor_id=user.id,
            is_open=is_open,
        )

    async def get_course_by_id(
            self,
            user: UserVerification,
            course_id: UUID,
    ) -> CourseResponse:
        course = await self.courses_manager.get_course_by_id(
            user,
            course_id,
        )

        if course:
            return CourseResponse.model_validate(
                course,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
            )
