from pathlib import Path
from shutil import rmtree
from uuid import UUID

from fastapi import Depends, UploadFile

from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.exceptions import ObjectMissingError
from server.app.api.v1.sections.sections_manager import SectionsManager
from server.app.api.v1.topics.topics import (
    TopicRawContent,
    TopicRenderedContent,
)
from server.app.api.v1.topics.topics_manager import TopicsManager
from server.data.courses_resources.compilation_manager import CompilationManager


class CoursesResourcesManager:
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
        self.courses_resources_directory_path = Path(
            __file__,
        ).parent / "resources"

        self.courses_manager = courses_manager
        self.sections_manager = sections_manager
        self.topics_manager = topics_manager
        self.compilation_manager = compilation_manager

    @staticmethod
    def create_object_directory(
            object_directory_path: Path,
    ) -> None:
        object_directory_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def delete_object_directory(
            self,
            object_directory_path: Path,
    ) -> None:
        result_path = self.courses_resources_directory_path / object_directory_path
        rmtree(
            result_path,
        )

    def get_course_directory_path(
            self,
            course_id: UUID,
    ) -> Path:
        return self.courses_resources_directory_path / str(
            course_id,
        )

    async def get_section_directory_path(
            self,
            section_id: UUID,
            course_id: UUID | None = None,
    ) -> Path:
        if course_id is None:
            section = await self.sections_manager.get_section_by_id(
                section_id,
            )
            course_id = section.course_id

        return self.get_course_directory_path(
            course_id,
        ) / str(
            section_id,
        )

    def get_topic_directory_path(
            self,
            topic_directory_path: str,
    ) -> Path:
        return self.courses_resources_directory_path / topic_directory_path

    def create_course_directory(
            self,
            course_id: UUID,
    ) -> None:
        self.create_object_directory(
            self.get_course_directory_path(
                course_id,
            ),
        )

    def delete_course_directory(
            self,
            course_id: UUID,
    ) -> None:
        self.delete_object_directory(
            self.get_course_directory_path(
                course_id,
            ),
        )

    async def create_section_directory(
            self,
            section_id: UUID,
            course_id: UUID | None = None,
    ) -> None:
        self.create_object_directory(
            await self.get_section_directory_path(
                section_id,
                course_id,
            ),
        )

    async def delete_section_directory(
            self,
            section_id: UUID,
            course_id: UUID | None = None,
    ) -> None:
        self.delete_object_directory(
            await self.get_section_directory_path(
                section_id,
                course_id,
            ),
        )

    def create_topic_directory(
            self,
            topic_directory_path: str,
    ) -> None:
        self.create_object_directory(
            self.get_topic_directory_path(
                topic_directory_path,
            ),
        )

    def delete_topic_directory(
            self,
            topic_directory_path: str,
    ) -> None:
        self.delete_object_directory(
            self.get_topic_directory_path(
                topic_directory_path,
            ),
        )

    async def compile_topic_rendered_content(
            self,
            topic_directory_path: str,
            raw_content: TopicRawContent,
            old_topic_rendered_content: TopicRenderedContent | None = None,
    ) -> TopicRenderedContent:
        full_topic_directory_path = self.courses_resources_directory_path / topic_directory_path

        return await self.compilation_manager.compile_topic_content(
            full_topic_directory_path,
            raw_content,
            old_topic_rendered_content,
        )

    async def get_topic_resource(
            self,
            topic_directory_path: str,
            resource_filename: str,
    ) -> Path:
        resource_filepath = self.courses_resources_directory_path / Path(
            topic_directory_path,
        ) / resource_filename

        if not resource_filepath.exists():
            raise ObjectMissingError(
                "Запрашиваемый ресурс не найден в файловой системе сервера!",
            )

        return resource_filepath

    def set_course_icon(
            self,
            course_id: UUID,
            icon_upload_file: UploadFile,
    ) -> None:
        course_path = self.get_course_directory_path(
            course_id,
        )
        icon_upload_file_filename = icon_upload_file.filename
        assert icon_upload_file_filename is not None
        icon_path = course_path / f"icon{Path(icon_upload_file_filename).suffix}"
        icon_file = icon_upload_file.file

        with open(
                icon_path,
                "wb",
        ) as icon_result_file:
            icon_result_file.write(
                icon_file.read(),
            )

        icon_file.close()

    def get_course_icon_path(
            self,
            course_id: UUID,
    ) -> Path:
        course_directory_path = self.get_course_directory_path(
            course_id,
        )
        for filepath in course_directory_path.iterdir():
            if filepath.is_file() and "icon" in filepath.name:
                return filepath

        raise ObjectMissingError(
            "Иконка курса не найдена!",
        )
