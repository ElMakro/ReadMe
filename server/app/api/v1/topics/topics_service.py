import uuid
from pathlib import Path
from uuid import UUID

from fastapi import Depends, UploadFile

from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.exceptions import BadRequestError, ConflictError, OperationPermissionError
from server.app.api.v1.sections.sections_manager import SectionsManager
from server.app.api.v1.topics.topics import (
    FileItem,
    TopicContent,
    TopicContentBlock,
    TopicIDMixin,
    TopicResponse,
    TopicsFullListResponse,
)
from server.app.api.v1.topics.topics_manager import TopicsManager
from server.app.api.v1.users.users import UserVerification
from server.app.api.v1.users.users_service import UsersService
from server.data.courses_resources.compilation_manager import CompilationError
from server.data.courses_resources.courses_resources_manager import CoursesResourcesManager
from server.enums.access_permissions import AccessPermissions


class TopicsService:
    def __init__(
            self,
            users_service: UsersService = Depends(
                UsersService,
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
            courses_resources_manager: CoursesResourcesManager = Depends(
                CoursesResourcesManager,
            ),
    ) -> None:
        self.users_service = users_service
        self.courses_manager = courses_manager
        self.sections_manager = sections_manager
        self.topics_manager = topics_manager
        self.courses_resources_manager = courses_resources_manager

    @staticmethod
    def construct_topic_directory_path(
            topic_id: UUID,
            section_id: UUID,
            course_id: UUID,
    ) -> Path:
        return Path(
            str(
                course_id,
            ),
        ) / Path(
            str(
                section_id,
            ),
        ) / Path(
            str(
                topic_id,
            ),
        )

    async def upload_resource(self, user: UserVerification, topic_id: UUID, block_number: int, file_number: int,
                              resource: UploadFile) -> FileItem:
        block_index, file_index = block_number - 1, file_number - 1

        topic, topic_response, session = await self.topics_manager.get_and_block_topic(topic_id)
        if (await self.users_service.check_course_access(user, course_id=topic_response.course_id)
                < AccessPermissions.EDIT_ACCESS):
            raise OperationPermissionError("У пользователя нет прав на загрузку ресурсов в данную тему!")

        try:
            block = topic_response.raw_content.root[block_index]
        except IndexError as error:
            raise ConflictError("Блока с таким порядковым номером не существует!") from error

        if block.type != "files":
            raise BadRequestError("Блок данного типа не позволяет хранить файлы!")

        try:
            file_item = block.content[file_index]
        except IndexError as error:
            raise ConflictError("Файла с таким порядковым номером не существует в теме!") from error

        if resource.filename != file_item.original_filename:
            raise ConflictError("У объявленного и загруженного файлов должны быть одинаковые имена!")

        assert resource.filename is not None
        server_filename = f"{uuid.uuid4()}{Path(resource.filename).suffix}"

        await self.courses_resources_manager.upload_topic_resource(topic_response.topic_directory_path, server_filename,
                                                             resource)

        modified_file_item = FileItem.model_construct(original_filename=resource.filename,
                                                      server_filename=server_filename)

        modified_block_content = block.content
        # noinspection PyTypeChecker
        modified_block_content[file_index] = modified_file_item

        modified_block = TopicContentBlock.model_construct(type="files", content=modified_block_content)

        modified_content = topic_response.raw_content.root
        modified_content[block_index] = modified_block
        modified_content = TopicContent.model_validate(modified_content)

        await self.topics_manager.change_topic_content_and_unblock(modified_content, topic, session)

        return modified_file_item

    async def get_resource(self, user: UserVerification | None, topic_id: UUID, resource_filename: str, ) -> Path:
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

    async def create_topic(
            self,
            user: UserVerification,
            section_id: UUID,
            name: str,
            order_number: int,
            tags: list[str],
            raw_content: TopicContent,
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
            raise ConflictError(
                "Тема с таким порядковым номером уже существует в этом разделе!",
            )

        topic_id = uuid.uuid4()

        topic_directory_path = self.construct_topic_directory_path(
            topic_id,
            section.id,
            course.id,
        )

        self.courses_resources_manager.create_topic_directory(
                topic_directory_path,
        )

        try:
            rendered_content = await self.courses_resources_manager.render_topic(
                    topic_directory_path,
                raw_content,
            )
        except CompilationError:
            self.courses_resources_manager.delete_topic_directory(topic_directory_path)
            raise

        topic = await self.topics_manager.create_topic(
            topic_id,
            section_id,
            name,
            order_number,
            course.id,
            tags,
            raw_content,
            rendered_content,
            topic_directory_path,
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
        ) < AccessPermissions.CONTENT_ACCESS:
            raise OperationPermissionError(
                "Пользователь не имеет доступа к данной теме!",
            )

        return topic

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
        ) < AccessPermissions.CONTENT_ACCESS:
            raise OperationPermissionError(
                "Пользователь не имеет доступа к темам данного раздела!",
            )

        return await self.topics_manager.get_topics_by_section_id(
            section_id,
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
        ) < AccessPermissions.CONTENT_ACCESS:
            raise OperationPermissionError(
                "Пользователь не имеет доступа к темам данного раздела!",
            )

        return await self.topics_manager.get_sections_by_course_id(
            course_id,
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

        self.courses_resources_manager.delete_topic_directory(
            topic.topic_directory_path,
        )

    async def update_topic(
            self,
            user: UserVerification,
            topic_id: UUID,
            new_name: str | None,
            new_tags: list[str] | None,
            new_raw_content: TopicContent
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

        result_name = new_name if new_name is not None else topic.name
        result_tags = new_tags if new_tags is not None else topic.tags

        rendered_content = await self.courses_resources_manager.render_topic(
            topic.topic_directory_path,
            new_raw_content,
        )

        await self.topics_manager.update_topic(
            topic_id,
            result_name,
            result_tags,
            new_raw_content,
            rendered_content,
        )
