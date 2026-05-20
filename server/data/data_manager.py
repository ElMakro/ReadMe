from pathlib import Path
from shutil import rmtree
from uuid import UUID

from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.sections.sections_manager import SectionsManager
from server.app.api.v1.topics.topics_manager import TopicsManager


# noinspection PyStringConversionWithoutDunderMethod
class DataManager:
    def __init__(
            self,
    ):
        self.content_path = Path(
            __file__,
        ) / "content"

        self.courses_manager = CoursesManager()
        self.sections_manager = SectionsManager()
        self.topics_manager = TopicsManager()

    def get_course_path(
            self,
            course_id: UUID,
    ) -> Path:
        return self.content_path / str(
            course_id,
        )

    async def get_section_path(
            self,
            section_id: UUID,
    ) -> Path:
        section = await self.sections_manager.get_section_by_id(
            section_id,
        )
        return self.content_path / str(
            section.course_id,
        ) / str(
            section_id,
        )

    async def get_topic_path(
            self,
            topic_id: UUID,
    ) -> Path:
        topic = await self.topics_manager.get_topic_by_id(
            topic_id,
        )
        section = await self.sections_manager.get_section_by_id(
            topic.section_id,
        )

        return self.content_path / str(
            section.course_id,
        ) / str(
            topic.section_id,
        ) / str(
            topic_id,
        )

    def create_course(
            self,
            course_id: UUID,
    ) -> None:
        course_path = self.get_course_path(
            course_id,
        )
        course_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def delete_course(
            self,
            course_id: UUID,
    ) -> None:
        course_path = self.get_course_path(
            course_id,
        )

        rmtree(
            course_path,
            ignore_errors=True,
        )

    async def create_section(
            self,
            section_id: UUID,
    ) -> None:
        section_path = await self.get_section_path(
            section_id,
        )
        section_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    async def delete_section(
            self,
            section_id: UUID,
    ) -> None:
        section_path = await self.get_section_path(
            section_id,
        )
        rmtree(
            section_path,
            ignore_errors=True,
        )

    async def create_topic(
            self,
            topic_id: UUID,
    ) -> None:
        topic_path = await self.get_topic_path(
            topic_id,
        )
        topic_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    async def delete_topic(
            self,
            topic_id: UUID,
    ) -> None:
        topic_path = await self.get_topic_path(
            topic_id,
        )

        rmtree(
            topic_path,
            ignore_errors=True,
        )
