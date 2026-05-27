from pathlib import Path

from fastapi import Depends

from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.exceptions import OperationPermissionError
from server.app.api.v1.sections.sections_manager import SectionsManager
from server.app.api.v1.topics.topics_manager import TopicsManager
from server.app.api.v1.users.users import UserVerification
from server.app.api.v1.users.users_service import UsersService
from server.data.courses_resources.courses_resources_files_manager import CoursesResourceFilesManager
from server.data.courses_resources.courses_resources_relation_manager import CoursesResourcesRelationManager
from server.data.courses_resources.courses_resources_service import CoursesResourcesService
from server.enums.access_permissions import AccessPermissions
from server.enums.object_type import ObjectType


class ContentService:
    def __init__(
            self,
            users_service: UsersService = Depends(
                UsersService,
            ),
            courses_resources_service: CoursesResourcesService = Depends(
                CoursesResourcesService,
            ),
            courses_manager: CoursesManager = Depends(
                CoursesManager,
            ),
            sections_manager: SectionsManager = Depends(
                SectionsManager,
            ),
            topics_manager: TopicsManager = Depends(
                TopicsManager,
            ),
            courses_resources_relation_manager: CoursesResourcesRelationManager = Depends(
                CoursesResourcesRelationManager,
            ),
            courses_resources_files_manager: CoursesResourceFilesManager = Depends(
                CoursesResourceFilesManager,
            ),
    ):
        self.users_service = users_service
        self.course_resources_service = courses_resources_service

        self.courses_manager = courses_manager
        self.sections_manager = sections_manager
        self.topics_manager = topics_manager

        self.courses_resources_relation_manager = courses_resources_relation_manager
        self.courses_resources_files_manager = courses_resources_files_manager

    async def get_course_resource(
            self,
            user: UserVerification | None,
            resource_filename: str,
    ) -> Path:
        resource_record = await self.courses_resources_relation_manager.get_resource_record_by_filename(
            resource_filename,
        )

        course_id = resource_record.parent_object_id

        match resource_record.parent_object_type:
            case ObjectType.COURSE:
                course_id = resource_record.parent_object_id

            case ObjectType.SECTION:
                section = await self.sections_manager.get_section_by_id(
                    resource_record.parent_object_id,
                )
                course_id = section.course_id
            case ObjectType.TOPIC:
                topic = await self.topics_manager.get_topic_by_id(
                    resource_record.parent_object_id,
                )
                course_id = topic.course_id

        if await self.users_service.check_course_access(
                user,
                course_id=course_id,
        ) < AccessPermissions.HEADER_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет прав на доступ к данному файлу",
            )

        return await self.courses_resources_files_manager.get_resource_filepath(
            resource_record.resource_filename,
        )
