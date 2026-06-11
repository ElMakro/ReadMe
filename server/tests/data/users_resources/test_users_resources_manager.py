import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from server.app.api.v1.exceptions import ObjectMissingError
from server.app.api.v1.users.users import CreatedUserInfo
from server.data.users_resources.users_resources_manager import UsersResourcesManager


class TestUsersResourcesManager:
    @pytest.fixture
    def mock_storage(self):
        storage = MagicMock()
        storage.get_absolute_path = MagicMock(side_effect=lambda p: Path(f"/tmp/{p}"))
        storage.create_directory = MagicMock()
        storage.save_file = MagicMock()
        storage.file_exists = MagicMock(return_value=True)
        storage.find_file_by_pattern = MagicMock(return_value=Path("/tmp/user/icon.png"))
        storage.delete_files_by_pattern = MagicMock()
        return storage

    @pytest.fixture
    def mock_icons_generator(self):
        generator = MagicMock()
        generator.generate_icon = MagicMock(return_value=b"fake_icon_data")
        return generator

    @pytest.fixture
    def manager(self, mock_storage, mock_icons_generator):
        return UsersResourcesManager(
            storage=mock_storage,
            icons_generator=mock_icons_generator,
        )

    @pytest.fixture
    def sample_user_info(self):
        return CreatedUserInfo(
            id=uuid.uuid4(),
            nickname="testuser",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    class TestGetRelativeUserDirectoryPath:
        def test_returns_path_with_user_id(self):
            user_id = uuid.uuid4()
            expected = Path(str(user_id))

            result = UsersResourcesManager.get_relative_user_directory_path(user_id)

            assert result == expected

    class TestGetAbsoluteUserDirectoryPath:
        def test_returns_absolute_path(self, manager, mock_storage):
            user_id = uuid.uuid4()
            expected = Path(f"/tmp/{user_id}")

            result = manager.get_absolute_user_directory_path(user_id)

            assert result == expected
            mock_storage.get_absolute_path.assert_called_once_with(Path(str(user_id)))

    class TestCreateUser:
        def test_creates_user_directory_and_icon_and_files_dir(self, manager, mock_storage,
                                                               mock_icons_generator, sample_user_info):
            user_dir = Path(f"/tmp/{sample_user_info.id}")

            manager.create_user(sample_user_info)

            mock_storage.get_absolute_path.assert_called_once()
            mock_storage.create_directory.assert_any_call(user_dir)
            mock_storage.create_directory.assert_any_call(user_dir / "files")

            expected_data = (f"{sample_user_info.id}-{sample_user_info.nickname}-{sample_user_info.created_at}-"
                             f"{sample_user_info.updated_at}")
            mock_icons_generator.generate_icon.assert_called_once_with(expected_data)
            mock_storage.save_file.assert_called_once_with(
                user_dir / "icon.png",
                b"fake_icon_data"
            )

    class TestGetUserIconPath:
        def test_returns_icon_path_when_exists(self, manager, mock_storage, sample_user_info):
            mock_storage.file_exists.return_value = True
            mock_storage.find_file_by_pattern.return_value = Path(f"/tmp/{sample_user_info.id}/icon.png")

            result = manager.get_user_icon_path(sample_user_info.id)

            assert result == Path(f"/tmp/{sample_user_info.id}/icon.png")
            mock_storage.file_exists.assert_called_once()
            mock_storage.find_file_by_pattern.assert_called_once_with(
                Path(f"/tmp/{sample_user_info.id}"), "icon"
            )

        def test_raises_error_when_user_directory_not_exists(self, manager, mock_storage, sample_user_info):
            mock_storage.file_exists.return_value = False

            with pytest.raises(ObjectMissingError, match="Пользователя с таким id не существует!"):
                manager.get_user_icon_path(sample_user_info.id)

        def test_raises_error_when_icon_not_found(self, manager, mock_storage, sample_user_info):
            mock_storage.file_exists.return_value = True
            mock_storage.find_file_by_pattern.return_value = None

            with pytest.raises(ObjectMissingError, match="Иконка пользователя не найдена!"):
                manager.get_user_icon_path(sample_user_info.id)

    class TestDeleteUserIcon:
        def test_deletes_icon_files(self, manager, mock_storage, sample_user_info):
            user_dir = Path(f"/tmp/{sample_user_info.id}")
            mock_storage.get_absolute_path.return_value = user_dir

            manager.delete_user_icon(sample_user_info.id)

            mock_storage.delete_files_by_pattern.assert_called_once_with(user_dir, "icon")

    class TestSetUserIcon:
        @pytest.mark.asyncio
        async def test_sets_user_icon_successfully(self, manager, mock_storage, sample_user_info):
            user_dir = Path(f"/tmp/{sample_user_info.id}")
            mock_storage.get_absolute_path.return_value = user_dir
            mock_storage.file_exists.return_value = True

            icon_file = AsyncMock()
            icon_file.filename = "new_icon.png"
            icon_file.read = AsyncMock(return_value=b"new_icon_data")

            await manager.set_user_icon(sample_user_info.id, icon_file)

            mock_storage.delete_files_by_pattern.assert_called_once_with(user_dir, "icon")
            mock_storage.save_file.assert_called_once_with(
                user_dir / "icon.png",
                b"new_icon_data"
            )

        @pytest.mark.asyncio
        async def test_sets_user_icon_with_different_extension(self, manager, mock_storage, sample_user_info):
            user_dir = Path(f"/tmp/{sample_user_info.id}")
            mock_storage.get_absolute_path.return_value = user_dir
            mock_storage.file_exists.return_value = True

            icon_file = AsyncMock()
            icon_file.filename = "icon.jpg"
            icon_file.read = AsyncMock(return_value=b"jpg_data")

            await manager.set_user_icon(sample_user_info.id, icon_file)

            mock_storage.save_file.assert_called_once_with(
                user_dir / "icon.jpg",
                b"jpg_data"
            )

        @pytest.mark.asyncio
        async def test_raises_error_when_user_not_exists(self, manager, mock_storage, sample_user_info):
            mock_storage.get_absolute_path.return_value = Path(f"/tmp/{sample_user_info.id}")
            mock_storage.file_exists.return_value = False

            icon_file = AsyncMock()
            icon_file.filename = "icon.png"

            with pytest.raises(ObjectMissingError, match="Пользователя с таким id не существует!"):
                await manager.set_user_icon(sample_user_info.id, icon_file)

            mock_storage.save_file.assert_not_called()

        @pytest.mark.asyncio
        async def test_raises_error_when_filename_empty(self, manager, mock_storage, sample_user_info):
            mock_storage.get_absolute_path.return_value = Path(f"/tmp/{sample_user_info.id}")
            mock_storage.file_exists.return_value = True

            icon_file = AsyncMock()
            icon_file.filename = None
            icon_file.read = AsyncMock(return_value=b"data")

            with pytest.raises(ValueError, match="Имя файла иконки не может быть пустым"):
                await manager.set_user_icon(sample_user_info.id, icon_file)

            mock_storage.save_file.assert_not_called()
