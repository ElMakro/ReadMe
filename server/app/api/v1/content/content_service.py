from pathlib import Path
from uuid import UUID

from fastapi import Depends

from server.app.api.v1.exceptions import OperationPermissionError
from server.app.api.v1.topics.topics_manager import TopicsManager
from server.app.api.v1.users.users import UserVerification
from server.app.api.v1.users.users_service import UsersService
from server.data.courses_resources.courses_resources_manager import CoursesResourcesManager
from server.enums.access_permissions import AccessPermissions


class ContentService:
    def __init__(
            self,
            users_service: UsersService = Depends(
                UsersService,
            ),
            courses_resources_manager: CoursesResourcesManager = Depends(
                CoursesResourcesManager,
            ),
            topics_manager: TopicsManager = Depends(
                TopicsManager,
            ),
    ):
        self.users_service = users_service
        self.courses_resources_manager = courses_resources_manager

        self.topics_manager = topics_manager

    async def get_topic_resource(
            self,
            user: UserVerification | None,
            topic_id: UUID,
            resource_filename: str,
    ) -> Path:
        topic = await self.topics_manager.get_topic_by_id(topic_id)

        if await self.users_service.check_course_access(
                user,
                course_id=topic.course_id,
        ) < AccessPermissions.HEADER_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет прав на доступ к данному файлу",
            )

        return await self.courses_resources_manager.get_topic_resource(
            topic.topic_directory_path,
            resource_filename,
        )
