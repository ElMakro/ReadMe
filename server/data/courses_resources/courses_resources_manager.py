from pathlib import Path
from uuid import UUID

from fastapi import Depends, UploadFile

from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.exceptions import ObjectMissingError
from server.app.api.v1.sections.sections_manager import SectionsManager
from server.app.api.v1.topics.topics import TopicContent
from server.app.api.v1.topics.topics_manager import TopicsManager
from server.data.courses_resources.compilation_manager import CompilationManager
from server.data.resource_storage import IResourceStorage, get_courses_resource_storage
from server.data.users_resources.icons_generator import IconsGenerator


class CoursesResourcesManager:
    def __init__(
            self,
            storage: IResourceStorage = Depends(get_courses_resource_storage),
            courses_manager: CoursesManager = Depends(CoursesManager),
            sections_manager: SectionsManager = Depends(SectionsManager),
            topics_manager: TopicsManager = Depends(TopicsManager),
            compilation_manager: CompilationManager = Depends(CompilationManager),
            icons_generator: IconsGenerator = Depends(IconsGenerator),
    ):
        self.storage = storage
        self.courses_manager = courses_manager
        self.sections_manager = sections_manager
        self.topics_manager = topics_manager
        self.compilation_manager = compilation_manager
        self.icons_generator = icons_generator

    @staticmethod
    def get_relative_course_directory_path(course_id: UUID) -> Path:
        return Path(str(course_id))

    async def get_relative_section_directory_path(
            self, section_id: UUID, course_id: UUID | None = None
    ) -> Path:
        if course_id is None:
            section = await self.sections_manager.get_section_by_id(section_id)
            course_id = section.course_id
        return self.get_relative_course_directory_path(course_id) / str(section_id)

    def create_course(self, course_id: UUID) -> None:
        self.create_course_directory(course_id)
        self.storage.save_file(self.get_relative_course_directory_path(course_id) / "icon.png",
                               self.icons_generator.generate_icon(f"{course_id}"))

    def create_course_directory(self, course_id: UUID) -> None:
        self.storage.create_directory(self.get_relative_course_directory_path(course_id))

    def delete_course_directory(self, course_id: UUID) -> None:
        self.storage.delete_directory(self.get_relative_course_directory_path(course_id))

    async def create_section_directory(
            self, section_id: UUID, course_id: UUID | None = None
    ) -> None:
        path = await self.get_relative_section_directory_path(section_id, course_id)
        self.storage.create_directory(path)

    async def delete_section_directory(
            self, section_id: UUID, course_id: UUID | None = None
    ) -> None:
        path = await self.get_relative_section_directory_path(section_id, course_id)
        self.storage.delete_directory(path)

    def create_topic_directory(self, topic_directory_path: Path) -> None:
        self.storage.create_directory(topic_directory_path)

    def delete_topic_directory(self, topic_directory_path: Path) -> None:
        self.storage.delete_directory(topic_directory_path)

    async def upload_topic_resource(
            self, topic_directory_path: Path, server_filename: str, resource: UploadFile
    ) -> None:
        filepath = topic_directory_path / server_filename
        content = await resource.read()
        self.storage.save_file(filepath, content)

    def delete_topic_resource(self, topic_directory_path: Path, server_filename: str) -> None:
        filepath = topic_directory_path / server_filename
        self.storage.delete_file(filepath)

    async def render_topic(
            self, topic_directory_path: Path, raw_content: TopicContent
    ) -> TopicContent:
        return await self.compilation_manager.compile_topic(topic_directory_path, raw_content)

    async def get_topic_resource(
            self, topic_directory_path: Path, resource_filename: str
    ) -> Path:
        filepath = topic_directory_path / resource_filename
        if not self.storage.file_exists(filepath):
            raise ObjectMissingError("Запрашиваемый ресурс не найден в файловой системе сервера!")
        return self.storage.get_absolute_path(filepath)

    def delete_course_icon(self, course_id: UUID) -> None:
        self.storage.delete_files_by_pattern(self.get_relative_course_directory_path(course_id), "icon")

    async def set_course_icon(
            self, course_id: UUID, icon_upload_file: UploadFile
    ) -> None:
        self.delete_course_icon(course_id)

        filename = icon_upload_file.filename
        if not filename:
            raise ValueError("Имя файла иконки не может быть пустым")

        icon_filename = f"icon{Path(filename).suffix}"
        icon_path = self.get_relative_course_directory_path(course_id) / icon_filename

        content = await icon_upload_file.read()
        self.storage.save_file(icon_path, content)

    def get_course_icon_path(self, course_id: UUID) -> Path:
        icon_path = self.storage.find_file_by_pattern(
            self.get_relative_course_directory_path(course_id), "icon"
        )
        if icon_path is None:
            raise ObjectMissingError("Иконка курса не найдена!")
        return icon_path
