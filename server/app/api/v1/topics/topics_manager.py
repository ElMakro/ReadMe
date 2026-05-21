from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, select

from server.app.api.v1.courses.courses_manager import ObjectExistenceError
from server.app.api.v1.topics.topics import TopicIDMixin, TopicResponse, TopicsFullListResponse
from server.config.db_dependency import DBDependency
from server.database.models import Topics


class TopicsManager:
    def __init__(
            self,
            db: DBDependency = Depends(
                DBDependency,
            ),
    ) -> None:
        self.db = db

    async def create_topic(
            self,
            section_id: UUID,
            name: str,
            order_number: int,
            course_id: UUID,
    ) -> TopicIDMixin:
        async with self.db.db_session() as session:
            topic = Topics(
                section_id=section_id,
                name=name,
                order_number=order_number,
                course_id=course_id,
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
            raise ObjectExistenceError(
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
                Topics.section_id == course_id,
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
            )

            await session.delete(
                topic,
            )
            await session.commit()

    async def update_topic(
            self,
            topic_id: UUID,
            name: str,
    ) -> None:
        async with self.db.db_session() as session:
            topic = await session.get(
                Topics,
                topic_id,
            )
            topic.name = name
            await session.commit()
