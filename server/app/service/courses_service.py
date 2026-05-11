from fastapi import Depends

from server.app.service.auth_handler import AuthHandler
from server.app.service.courses_manager import CoursesManager


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
