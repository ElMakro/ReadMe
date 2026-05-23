from uuid import UUID

from fastapi import Depends
from fastapi.responses import FileResponse

from server.app.api.v1.courses.courses_service import OperationPermissionError
from server.app.api.v1.topics.topics_manager import TopicsManager
from server.app.api.v1.users.enums.access_permissions import AccessPermissions
from server.app.api.v1.users.users import UserVerification
from server.app.api.v1.users.users_service import UsersService
from server.data.data_manager import DataManager


class ContentService:
    def __init__(
            self,
            users_service: UsersService = Depends(
                UsersService,
            ),
            topics_manager: TopicsManager = Depends(
                TopicsManager,
            ),
            data_manager: DataManager = Depends(
                DataManager,
            ),
    ):
        self.users_service = users_service
        self.topics_manager = topics_manager
        self.data_manager = data_manager

    async def get_topic_file(
            self,
            user: UserVerification | None,
            topic_id: UUID,
            file_name: str,
    ) -> FileResponse:
        topic = await self.topics_manager.get_topic_by_id(
            topic_id,
        )

        if await self.users_service.check_course_access(
                user,
                course_id=topic.course_id,
        ) < AccessPermissions.CONTENT_ACCESS:
            raise OperationPermissionError(
                "У пользователя недостаточно прав на получение контента темы!",
            )

        return await self.data_manager.get_topic_file(
            file_name,
            topic_id,
            topic.section_id,
            topic.course_id,
        )
