from uuid import UUID

from fastapi import Depends

from server.app.api.v1.topics.topics import (
    TopicRawContent,
    TopicRenderedContent,
)
from server.data.courses_resources.compilation_manager import CompilationManager
from server.data.courses_resources.courses_resources_relation_manager import CoursesResourcesRelationManager
from server.enums.object_type import ObjectType


class CoursesResourcesService:
    def __init__(
            self,
            compilation_manager: CompilationManager = Depends(
                CompilationManager,
            ),
            courses_resources_relation_manager: CoursesResourcesRelationManager = Depends(
                CoursesResourcesRelationManager,
            ),
    ):

        self.compilation_manager = compilation_manager

        self.courses_resources_relation_manager = courses_resources_relation_manager

    async def compile_and_register_topic_rendered_content(
            self,
            topic_id: UUID,
            raw_content: TopicRawContent,
            old_topic_rendered_content: TopicRenderedContent | None = None,
    ) -> TopicRenderedContent:
        rendered_content = await self.compilation_manager.compile_topic_content(
            raw_content,
            old_topic_rendered_content,
        )

        for block in rendered_content.root:
            if block.type == "file":
                await self.courses_resources_relation_manager.register_resource_record(
                    block.rendered_content,
                    topic_id,
                    ObjectType.TOPIC,
                )

        return rendered_content
