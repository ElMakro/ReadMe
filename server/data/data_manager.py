import json
from pathlib import Path
from shutil import rmtree
from uuid import UUID

from fastapi import Depends
from fastapi.responses import FileResponse

from server.app.api.v1.courses.courses_manager import CoursesManager, ObjectExistenceError
from server.app.api.v1.sections.sections_manager import SectionsManager
from server.app.api.v1.topics.topics import (
    TopicRawContent,
    TopicRenderedContent,
)
from server.app.api.v1.topics.topics_manager import TopicsManager
from server.data.compilation_manager import CompilationManager


class UnsupportedMediaTypeError(
    ValueError,
):
    """Исключение, связанное с неподдерживаемым для передачи типом файла"""


# noinspection PyStringConversionWithoutDunderMethod
class DataManager:
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
            compilation_manager: CompilationManager = Depends(
                CompilationManager,
            ),
    ):
        self.content_path = Path(
            __file__,
        ).parent / "content"

        self.courses_manager = courses_manager
        self.sections_manager = sections_manager
        self.topics_manager = topics_manager
        self.compilation_manager = compilation_manager

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
            course_id: UUID | None = None,
    ) -> Path:
        if course_id is None:
            section = await self.sections_manager.get_section_by_id(
                section_id,
            )
            course_id = section.course_id

        return self.content_path / str(
            course_id,
        ) / str(
            section_id,
        )

    async def get_topic_path(
            self,
            topic_id: UUID,
            section_id: UUID | None = None,
            course_id: UUID | None = None,
    ) -> Path:
        if section_id is None or course_id is None:
            topic = await self.topics_manager.get_topic_by_id(
                topic_id,
            )
            section_id = topic.section_id
            course_id = topic.course_id

        return self.content_path / str(
            course_id,
        ) / str(
            section_id,
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
            course_id: UUID | None = None,
    ) -> None:
        section_path = await self.get_section_path(
            section_id,
            course_id,
        )
        section_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    async def delete_section(
            self,
            section_id: UUID,
            course_id: UUID | None = None,
    ) -> None:
        section_path = await self.get_section_path(
            section_id,
            course_id,
        )
        rmtree(
            section_path,
            ignore_errors=True,
        )

    async def create_topic(
            self,
            topic_id: UUID,
            section_id: UUID | None = None,
            course_id: UUID | None = None,
    ) -> None:
        topic_path = await self.get_topic_path(
            topic_id,
            section_id,
            course_id,
        )
        topic_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        topic_raw_content_json_path = topic_path / "raw_content.json"
        topic_raw_content_json_path.touch(
            exist_ok=True,
        )
        with open(
                topic_raw_content_json_path,
                "w",
                encoding="utf-8",
        ) as raw_content_file:
            json.dump(
                [],
                raw_content_file,
                ensure_ascii=False,
                indent=4,
            )

        topic_rendered_content_json_path = topic_path / "rendered_content.json"
        topic_rendered_content_json_path.touch(
            exist_ok=True,
        )
        with open(
                topic_rendered_content_json_path,
                "w",
                encoding="utf-8",
        ) as rendered_content_file:
            json.dump(
                [],
                rendered_content_file,
                ensure_ascii=False,
                indent=4,
            )

    async def delete_topic(
            self,
            topic_id: UUID,
            section_id: UUID | None = None,
            course_id: UUID | None = None,
    ) -> None:
        topic_path = await self.get_topic_path(
            topic_id,
            section_id,
            course_id,
        )

        rmtree(
            topic_path,
            ignore_errors=True,
        )

    async def update_topic_content(
            self,
            topic_raw_content: TopicRawContent,
            topic_id: UUID,
            section_id: UUID | None = None,
            course_id: UUID | None = None,
    ) -> None:
        topic_path = await self.get_topic_path(
            topic_id,
            section_id,
            course_id,
        )

        topic_rendered_content = await self.compilation_manager.compile_content(
            topic_path,
            topic_raw_content,
        )

        topic_raw_content_json_path = topic_path / "raw_content.json"
        topic_rendered_content_json_path = topic_path / "rendered_content.json"

        with open(
                topic_raw_content_json_path,
                "w",
                encoding="utf-8",
        ) as topic_raw_content_json_file:
            json.dump(
                topic_raw_content.model_dump(),
                topic_raw_content_json_file,
                indent=4,
                ensure_ascii=False,
            )

        with open(
                topic_rendered_content_json_path,
                "w",
                encoding="utf-8",
        ) as topic_rendered_content_json_file:
            json.dump(
                topic_rendered_content.model_dump(),
                topic_rendered_content_json_file,
                indent=4,
                ensure_ascii=False,
            )

    async def get_topic_raw_content(
            self,
            topic_id: UUID,
            section_id: UUID | None,
            course_id: UUID | None,
    ) -> TopicRawContent:
        topic_path = await self.get_topic_path(
            topic_id,
            section_id,
            course_id,
        )
        raw_content_file_path = topic_path / "raw_content.json"
        with open(
                raw_content_file_path,
                encoding="utf-8",
        ) as raw_content_file:
            raw_content = json.load(
                raw_content_file,
            )

        return TopicRawContent.model_validate(
            raw_content,
        )

    async def get_topic_rendered_content(
            self,
            topic_id: UUID,
            section_id: UUID | None,
            course_id: UUID | None,
    ) -> TopicRenderedContent:
        topic_path = await self.get_topic_path(
            topic_id,
            section_id,
            course_id,
        )
        rendered_content_file_path = topic_path / "rendered_content.json"
        with open(
                rendered_content_file_path,
                encoding="utf-8",
        ) as rendered_content_file:
            rendered_content = json.load(
                rendered_content_file,
            )

        return TopicRenderedContent.model_validate(
            rendered_content,
        )

    async def get_topic_file(
            self,
            file_name: str,
            topic_id: UUID,
            section_id: UUID | None = None,
            course_id: UUID | None = None,
    ) -> FileResponse:
        topic_path = await self.get_topic_path(
            topic_id,
            section_id,
            course_id,
        )
        file_path = topic_path / file_name
        if not file_path.exists():
            raise ObjectExistenceError(
                "Запрашиваемый файл не найден!",
            )

        return FileResponse(
            file_path,
        )
