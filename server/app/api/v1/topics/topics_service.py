from uuid import UUID

from fastapi import Depends

from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.courses.courses_service import OperationPermissionError
from server.app.api.v1.sections.sections_manager import SectionsManager
from server.app.api.v1.sections.sections_service import OrderNumberConflictError
from server.app.api.v1.topics.topics import (
    TopicIDMixin,
    TopicRawContent,
    TopicRenderedContent,
    TopicResponse,
    TopicsFullListResponse,
)
from server.app.api.v1.topics.topics_manager import TopicsManager
from server.app.api.v1.users.enums.access_permissions import AccessPermissions
from server.app.api.v1.users.users import UserVerification
from server.app.api.v1.users.users_service import UsersService
from server.data.data_manager import DataManager


class TopicsService:
    def __init__(
            self,
            courses_manager: CoursesManager = Depends(
                CoursesManager,
            ),
            sections_manager: SectionsManager = Depends(
                SectionsManager,
            ),
            topics_manager: TopicsManager = Depends(
                TopicsManager,
            ),
            data_manager: DataManager = Depends(
                DataManager,
            ),
            users_service: UsersService = Depends(
                UsersService,
            ),
    ) -> None:
        self.courses_manager = courses_manager
        self.sections_manager = sections_manager
        self.topics_manager = topics_manager
        self.data_manager = data_manager
        self.users_service = users_service

    async def create_topic(
            self,
            user: UserVerification,
            section_id: UUID,
            name: str,
            order_number: int,
            tags: list[str],
    ) -> TopicIDMixin:
        section = await self.sections_manager.get_section_by_id(
            section_id,
        )
        course = await self.courses_manager.get_course_by_id(
            section.course_id,
        )

        if await self.users_service.check_course_access(
                user,
                course=course,
        ) < AccessPermissions.EDIT_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет права на создание темы в данном курсе!",
            )

        if await self.topics_manager.check_section_have_topic_with_order_number(
                section_id,
                order_number, ):
            raise OrderNumberConflictError(
                "Тема с таким порядковым номером уже существует в этом разделе!",
            )

        topic = await self.topics_manager.create_topic(
            section_id,
            name,
            order_number,
            course.id,
            tags,
        )

        await self.data_manager.create_topic(
            topic.id,
            section_id,
            course.id,
        )

        return topic

    async def get_topic_by_id(
            self,
            user: UserVerification | None,
            topic_id: UUID,
    ) -> TopicResponse:
        topic = await self.topics_manager.get_topic_by_id(
            topic_id,
        )

        if await self.users_service.check_course_access(
                user,
                course_id=topic.course_id,
        ) > AccessPermissions.CONTENT_ACCESS:
            return topic

        raise OperationPermissionError(
            "Пользователь не имеет доступа к данной теме!",
        )

    async def get_topics_by_section_id(
            self,
            user: UserVerification | None,
            section_id: UUID,
    ) -> TopicsFullListResponse:
        section = await self.sections_manager.get_section_by_id(
            section_id,
        )

        if await self.users_service.check_course_access(
                user,
                course_id=section.course_id,
        ) > AccessPermissions.CONTENT_ACCESS:
            return await self.topics_manager.get_topics_by_section_id(
                section_id,
            )

        raise OperationPermissionError(
            "Пользователь не имеет доступа к темам данного раздела!",
        )

    async def get_topics_by_course_id(
            self,
            user: UserVerification | None,
            course_id: UUID,
    ) -> TopicsFullListResponse:
        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if await self.users_service.check_course_access(
                user,
                course=course,
        ) > AccessPermissions.CONTENT_ACCESS:
            return await self.topics_manager.get_sections_by_course_id(
                course_id,
            )

        raise OperationPermissionError(
            "Пользователь не имеет доступа к темам данного раздела!",
        )

    async def delete_topic(
            self,
            user: UserVerification,
            topic_id: UUID,
    ) -> None:
        topic = await self.topics_manager.get_topic_by_id(
            topic_id,
        )

        if await self.users_service.check_course_access(
                user,
                course_id=topic.course_id,
        ) < AccessPermissions.EDIT_ACCESS:
            raise OperationPermissionError(
                "Пользователь не имеет права на удаление этой темы!",
            )

        await self.topics_manager.delete_topic(
            topic_id,
        )

        await self.data_manager.delete_topic(
            topic_id,
            topic.section_id,
            topic.course_id,
        )

    async def update_topic(
            self,
            user: UserVerification,
            topic_id: UUID,
            new_name: str | None,
            new_tags: list[str] | None,
    ) -> None:
        topic = await self.topics_manager.get_topic_by_id(
            topic_id,
        )

        if await self.users_service.check_course_access(
                user,
                course_id=topic.course_id,
        ) < AccessPermissions.EDIT_ACCESS:
            raise OperationPermissionError(
                "Пользователь не имеет права на изменение темы!",
            )

        if new_name is None and new_tags is None:
            return

        result_name = new_name if new_name is not None else topic.name
        result_tags = new_tags if new_tags is not None else topic.tags

        if topic.name == result_name and topic.tags == result_tags:
            return

        await self.topics_manager.update_topic(
            topic_id,
            result_name,
            result_tags,
        )

    async def get_raw_content(
            self,
            user: UserVerification | None,
            topic_id: UUID,
    ) -> TopicRawContent:
        topic = await self.topics_manager.get_topic_by_id(
            topic_id,
        )

        if await self.users_service.check_course_access(
                user,
                course_id=topic.course_id,
        ) < AccessPermissions.EDIT_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет разрешения на просмотр контента!",
            )

        return await self.data_manager.get_topic_raw_content(
            topic.id,
            topic.section_id,
            topic.course_id, )

    async def get_rendered_content(
            self,
            user: UserVerification | None,
            topic_id: UUID,
    ) -> TopicRenderedContent:
        topic = await self.topics_manager.get_topic_by_id(
            topic_id,
        )

        if await self.users_service.check_course_access(
                user,
                course_id=topic.course_id,
        ) < AccessPermissions.CONTENT_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет разрешения на просмотр контента!",
            )

        return await self.data_manager.get_topic_rendered_content(
            topic.id,
            topic.section_id,
            topic.course_id, )

    async def put_topic_content(
            self,
            user: UserVerification,
            topic_id: UUID,
            topic_raw_content: TopicRawContent,
    ) -> None:
        topic = await self.topics_manager.get_topic_by_id(
            topic_id,
        )

        if await self.users_service.check_course_access(
                user,
                course_id=topic.course_id,
        ) < AccessPermissions.EDIT_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет разрешения на установку контента курса!",
            )

        await self.data_manager.update_topic_content(
            topic_raw_content,
            topic_id,
            topic.section_id,
            topic.course_id,
        )
