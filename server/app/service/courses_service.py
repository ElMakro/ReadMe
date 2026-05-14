from fastapi import Depends

from server.app.service.auth_handler import AuthHandler
from server.app.service.courses_manager import CoursesManager
from server.schemas.courses import CoursesList
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

    async def get_courses_for_user(self, user: UserVerification, page: int, size: int) -> CoursesList:
        offset = (page - 1) * size
        limit = size
        return await self.courses_manager.get_courses_of_user(user.id, offset, limit)
