import uuid
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, select

from server.app.api.v1.exceptions import ObjectMissingError
from server.app.api.v1.topics.topics import (
    TopicIDMixin,
    TopicRawContent,
    TopicRenderedContent,
    TopicResponse,
    TopicsFullListResponse,
)
from server.config.db_dependency import DBDependency
from server.data.courses_resources.courses_resources_service import CoursesResourcesService
from server.database.models import Topics


class TopicsManager:
    def __init__(
            self,
            db: DBDependency = Depends(
                DBDependency,
            ),
            courses_resources_manager: CoursesResourcesService = Depends(
                CoursesResourcesService,
            ),
    ) -> None:
        self.db = db
        self.courses_resources_manager = courses_resources_manager

    async def create_topic(
            self,
            section_id: UUID,
            name: str,
            order_number: int,
            course_id: UUID,
            tags: list[str],
            raw_content: TopicRawContent,
    ) -> TopicIDMixin:
        topic_id = uuid.uuid4()
        rendered_content = await self.courses_resources_manager.compile_and_register_topic_rendered_content(
            topic_id,
            raw_content,
            None,
        )

        async with self.db.db_session() as session:
            topic = Topics(
                id=topic_id,
                section_id=section_id,
                name=name,
                order_number=order_number,
                course_id=course_id,
                tags=tags,
                raw_content=[block.model_dump() for block in raw_content.root],
                rendered_content=[block.model_dump() for block in rendered_content.root],
            )

            session.add(
                topic,
            )
            await session.commit()

        return TopicIDMixin.model_construct(
            id=topic.id,
        )

    async def get_topic_by_id(
            self,
            topic_id: UUID,
    ) -> TopicResponse:
        async with self.db.db_session() as session:
            topic = await session.get(
                Topics,
                topic_id,
            )

        if topic is None:
            raise ObjectMissingError(
                "Темы с таким id не существует!",
            )

        return TopicResponse.model_validate(
            topic,
        )

    async def check_section_have_topic_with_order_number(
            self,
            section_id: UUID,
            order_number: int,
    ) -> bool:
        async with self.db.db_session() as session:
            query = select(
                Topics,
            ).where(
                and_(
                    Topics.section_id == section_id,
                    Topics.order_number == order_number,
                ),
            )

            result = await session.execute(
                query,
            )

        return bool(
            result.one_or_none(),
        )

    async def get_topics_by_section_id(
            self,
            section_id: UUID,
    ) -> TopicsFullListResponse:
        async with self.db.db_session() as session:
            query = select(
                Topics,
            ).where(
                Topics.section_id == section_id,
            )

            result = await session.execute(
                query,
            )

            topics = result.scalars().all()

        return TopicsFullListResponse.model_validate(
            topics,
        )

    async def get_sections_by_course_id(
            self,
            course_id: UUID,
    ) -> TopicsFullListResponse:
        async with self.db.db_session() as session:
            query = select(
                Topics,
            ).where(
                Topics.course_id == course_id,
            )

            result = await session.execute(
                query,
            )

            topics = result.scalars().all()

        return TopicsFullListResponse.model_validate(
            topics,
        )

    async def delete_topic(
            self,
            topic_id: UUID,
    ) -> None:
        async with self.db.db_session() as session:
            topic = await session.get(
                Topics,
                topic_id,
                with_for_update=True,
            )

            await session.delete(
                topic,
            )
            await session.commit()

    async def update_topic(
            self,
            topic_id: UUID,
            name: str,
            tags: list[str],
            raw_content: TopicRawContent,
    ) -> None:
        async with self.db.db_session() as session:
            topic = await session.get(
                Topics,
                topic_id,
                with_for_update=True,
            )

            topic_response = TopicResponse.model_validate(
                topic,
            )

            assert topic is not None

            rendered_content = await self.courses_resources_manager.compile_and_register_topic_rendered_content(
                topic_response.id,
                raw_content,
                TopicRenderedContent.model_validate(
                    topic.rendered_content,
                ),
            )

            topic.name = name
            topic.tags = tags
            topic.raw_content = [block.model_dump() for block in raw_content.root]
            topic.rendered_content = [block.model_dump() for block in rendered_content.root]

            await session.commit()
