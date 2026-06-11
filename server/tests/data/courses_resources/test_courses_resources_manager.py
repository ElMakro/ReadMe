import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from server.app.api.v1.exceptions import ObjectMissingError
from server.data.courses_resources.courses_resources_manager import CoursesResourcesManager


class TestCoursesResourcesManager:
    @pytest.fixture
    def mock_storage(self):
        storage = MagicMock()
        storage.create_directory = MagicMock()
        storage.delete_directory = MagicMock()
        storage.save_file = MagicMock()
        storage.delete_file = MagicMock()
        storage.file_exists = MagicMock(return_value=True)
        storage.find_file_by_pattern = MagicMock(return_value=Path("icon.png"))
        storage.delete_files_by_pattern = MagicMock()
        storage.get_absolute_path = MagicMock(side_effect=lambda p: Path(f"/absolute/{p}"))
        return storage

    @pytest.fixture
    def mock_courses_manager(self):
        return AsyncMock()

    @pytest.fixture
    def mock_sections_manager(self):
        manager = AsyncMock()
        manager.get_section_by_id = AsyncMock()
        return manager

    @pytest.fixture
    def mock_topics_manager(self):
        return AsyncMock()

    @pytest.fixture
    def mock_compilation_manager(self):
        return AsyncMock()

    @pytest.fixture
    def mock_icons_generator(self):
        generator = MagicMock()
        generator.generate_icon = MagicMock(return_value=b"fake_icon")
        return generator

    @pytest.fixture
    def manager(
            self,
            mock_storage,
            mock_courses_manager,
            mock_sections_manager,
            mock_topics_manager,
            mock_compilation_manager,
            mock_icons_generator,
    ):
        return CoursesResourcesManager(
            storage=mock_storage,
            courses_manager=mock_courses_manager,
            sections_manager=mock_sections_manager,
            topics_manager=mock_topics_manager,
            compilation_manager=mock_compilation_manager,
            icons_generator=mock_icons_generator,
        )

    class TestGetRelativeCourseDirectoryPath:
        def test_returns_path_with_course_id(self):
            course_id = uuid.uuid4()
            expected = Path(str(course_id))

            result = CoursesResourcesManager.get_relative_course_directory_path(course_id)

            assert result == expected

    class TestGetRelativeSectionDirectoryPath:
        @pytest.mark.asyncio
        async def test_returns_path_with_course_and_section_ids(self, manager, mock_sections_manager):
            course_id = uuid.uuid4()
            section_id = uuid.uuid4()

            result = await manager.get_relative_section_directory_path(section_id, course_id)

            assert result == Path(str(course_id)) / str(section_id)
            mock_sections_manager.get_section_by_id.assert_not_called()

        @pytest.mark.asyncio
        async def test_fetches_course_id_when_not_provided(self, manager, mock_sections_manager):
            section_id = uuid.uuid4()
            mock_section = MagicMock()
            mock_section.course_id = uuid.uuid4()
            mock_sections_manager.get_section_by_id.return_value = mock_section

            result = await manager.get_relative_section_directory_path(section_id)

            assert result == Path(str(mock_section.course_id)) / str(section_id)
            mock_sections_manager.get_section_by_id.assert_awaited_once_with(section_id)

    class TestCreateCourse:
        def test_creates_course_directory_and_icon(self, manager, mock_storage, mock_icons_generator):
            course_id = uuid.uuid4()

            manager.create_course(course_id)

            mock_storage.create_directory.assert_called_once()
            mock_storage.save_file.assert_called_once()
            mock_icons_generator.generate_icon.assert_called_once_with(str(course_id))

    class TestCreateCourseDirectory:
        def test_creates_directory(self, manager, mock_storage):
            course_id = uuid.uuid4()

            manager.create_course_directory(course_id)

            mock_storage.create_directory.assert_called_once_with(Path(str(course_id)))

    class TestDeleteCourseDirectory:
        def test_deletes_directory(self, manager, mock_storage):
            course_id = uuid.uuid4()

            manager.delete_course_directory(course_id)

            mock_storage.delete_directory.assert_called_once_with(Path(str(course_id)))

    class TestCreateSectionDirectory:
        @pytest.mark.asyncio
        async def test_creates_section_directory(self, manager, mock_storage):
            section_id = uuid.uuid4()
            course_id = uuid.uuid4()

            await manager.create_section_directory(section_id, course_id)

            expected_path = Path(str(course_id)) / str(section_id)
            mock_storage.create_directory.assert_called_once_with(expected_path)

    class TestDeleteSectionDirectory:
        @pytest.mark.asyncio
        async def test_deletes_section_directory(self, manager, mock_storage):
            section_id = uuid.uuid4()
            course_id = uuid.uuid4()

            await manager.delete_section_directory(section_id, course_id)

            expected_path = Path(str(course_id)) / str(section_id)
            mock_storage.delete_directory.assert_called_once_with(expected_path)

    class TestCreateTopicDirectory:
        def test_creates_topic_directory(self, manager, mock_storage):
            topic_path = Path("/test/topic")

            manager.create_topic_directory(topic_path)

            mock_storage.create_directory.assert_called_once_with(topic_path)

    class TestDeleteTopicDirectory:
        def test_deletes_topic_directory(self, manager, mock_storage):
            topic_path = Path("/test/topic")

            manager.delete_topic_directory(topic_path)

            mock_storage.delete_directory.assert_called_once_with(topic_path)

    class TestUploadTopicResource:
        @pytest.mark.asyncio
        async def test_uploads_resource(self, manager, mock_storage):
            topic_path = Path("/test/topic")
            server_filename = "uuid.txt"
            resource = AsyncMock()
            resource.read = AsyncMock(return_value=b"test content")

            await manager.upload_topic_resource(topic_path, server_filename, resource)

            expected_path = topic_path / server_filename
            mock_storage.save_file.assert_called_once_with(expected_path, b"test content")

    class TestDeleteTopicResource:
        def test_deletes_resource(self, manager, mock_storage):
            topic_path = Path("/test/topic")
            server_filename = "uuid.txt"

            manager.delete_topic_resource(topic_path, server_filename)

            expected_path = topic_path / server_filename
            mock_storage.delete_file.assert_called_once_with(expected_path)

    class TestRenderTopic:
        @pytest.mark.asyncio
        async def test_renders_topic(self, manager, mock_compilation_manager):
            topic_path = Path("/test/topic")
            raw_content = MagicMock()
            expected_result = MagicMock()
            mock_compilation_manager.compile_topic.return_value = expected_result

            result = await manager.render_topic(topic_path, raw_content)

            assert result == expected_result
            mock_compilation_manager.compile_topic.assert_awaited_once_with(topic_path, raw_content)

    class TestGetTopicResource:
        @pytest.mark.asyncio
        async def test_returns_resource_path_when_exists(self, manager, mock_storage):
            topic_path = Path("/test/topic")
            resource_filename = "file.txt"
            mock_storage.file_exists.return_value = True
            mock_storage.get_absolute_path.return_value = Path("/absolute/test/topic/file.txt")

            result = await manager.get_topic_resource(topic_path, resource_filename)

            assert result == Path("/absolute/test/topic/file.txt")
            mock_storage.file_exists.assert_called_once_with(topic_path / resource_filename)

        @pytest.mark.asyncio
        async def test_raises_error_when_not_exists(self, manager, mock_storage):
            topic_path = Path("/test/topic")
            resource_filename = "not_exist.txt"
            mock_storage.file_exists.return_value = False

            with pytest.raises(ObjectMissingError, match="Запрашиваемый ресурс не найден"):
                await manager.get_topic_resource(topic_path, resource_filename)

    class TestDeleteCourseIcon:
        def test_deletes_icon_files(self, manager, mock_storage):
            course_id = uuid.uuid4()

            manager.delete_course_icon(course_id)

            mock_storage.delete_files_by_pattern.assert_called_once_with(Path(str(course_id)), "icon")

    class TestSetCourseIcon:
        @pytest.mark.asyncio
        async def test_sets_course_icon_successfully(self, manager, mock_storage):
            course_id = uuid.uuid4()
            icon_file = AsyncMock()
            icon_file.filename = "icon.png"
            icon_file.read = AsyncMock(return_value=b"new_icon")

            await manager.set_course_icon(course_id, icon_file)

            mock_storage.delete_files_by_pattern.assert_called_once_with(Path(str(course_id)), "icon")
            mock_storage.save_file.assert_called_once_with(
                Path(str(course_id)) / "icon.png",
                b"new_icon"
            )

        @pytest.mark.asyncio
        async def test_sets_course_icon_with_different_extension(self, manager, mock_storage):
            course_id = uuid.uuid4()
            icon_file = AsyncMock()
            icon_file.filename = "icon.jpg"
            icon_file.read = AsyncMock(return_value=b"jpg_data")

            await manager.set_course_icon(course_id, icon_file)

            mock_storage.save_file.assert_called_once_with(
                Path(str(course_id)) / "icon.jpg",
                b"jpg_data"
            )

        @pytest.mark.asyncio
        async def test_raises_error_when_filename_empty(self, manager, mock_storage):
            course_id = uuid.uuid4()
            icon_file = AsyncMock()
            icon_file.filename = None

            with pytest.raises(ValueError, match="Имя файла иконки не может быть пустым"):
                await manager.set_course_icon(course_id, icon_file)

    class TestGetCourseIconPath:
        def test_returns_icon_path_when_found(self, manager, mock_storage):
            course_id = uuid.uuid4()
            mock_storage.find_file_by_pattern.return_value = Path("icon.png")

            result = manager.get_course_icon_path(course_id)

            assert result == Path("icon.png")
            mock_storage.find_file_by_pattern.assert_called_once_with(Path(str(course_id)), "icon")

        def test_raises_error_when_not_found(self, manager, mock_storage):
            course_id = uuid.uuid4()
            mock_storage.find_file_by_pattern.return_value = None

            with pytest.raises(ObjectMissingError, match="Иконка курса не найдена!"):
                manager.get_course_icon_path(course_id)
