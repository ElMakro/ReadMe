from pathlib import Path

import pytest

from server.data.resource_storage import (
    LocalFileSystemStorage,
    get_courses_resource_storage,
    get_users_resource_storage,
)


class TestLocalFileSystemStorage:
    @pytest.fixture
    def storage(self, tmp_path):
        return LocalFileSystemStorage(tmp_path)

    def test_create_directory(self, storage, tmp_path):
        path = Path("test_dir")

        storage.create_directory(path)

        assert (tmp_path / path).exists()
        assert (tmp_path / path).is_dir()

    def test_create_directory_nested(self, storage, tmp_path):
        path = Path("level1/level2/level3")

        storage.create_directory(path)

        assert (tmp_path / path).exists()
        assert (tmp_path / path).is_dir()

    def test_create_directory_already_exists(self, storage, tmp_path):
        path = Path("existing_dir")
        (tmp_path / path).mkdir()

        storage.create_directory(path)  # не должно вызвать ошибку

        assert (tmp_path / path).exists()

    def test_save_file(self, storage, tmp_path):
        path = Path("test.txt")
        content = b"Hello, World!"

        storage.save_file(path, content)

        saved_path = tmp_path / path
        assert saved_path.exists()
        assert saved_path.read_bytes() == content

    def test_save_file_in_nested_directory(self, storage, tmp_path):
        path = Path("dir1/dir2/file.txt")
        content = b"Nested file content"

        storage.save_file(path, content)

        saved_path = tmp_path / path
        assert saved_path.exists()
        assert saved_path.read_bytes() == content

    def test_delete_file(self, storage, tmp_path):
        path = Path("to_delete.txt")
        (tmp_path / path).write_bytes(b"data")

        storage.delete_file(path)

        assert not (tmp_path / path).exists()

    def test_delete_file_not_exists(self, storage):
        path = Path("not_exists.txt")

        storage.delete_file(path)  # не должно вызвать ошибку

    def test_file_exists(self, storage, tmp_path):
        path = Path("exists.txt")
        assert storage.file_exists(path) is False

        (tmp_path / path).write_bytes(b"data")
        assert storage.file_exists(path) is True

    def test_delete_files_by_pattern(self, storage, tmp_path):
        storage.save_file(Path("icon1.png"), b"data1")
        storage.save_file(Path("icon2.jpg"), b"data2")
        storage.save_file(Path("data.txt"), b"data3")

        storage.delete_files_by_pattern(Path("."), "icon")

        assert not (tmp_path / "icon1.png").exists()
        assert not (tmp_path / "icon2.jpg").exists()
        assert (tmp_path / "data.txt").exists()

    def test_find_file_by_pattern(self, storage, tmp_path):
        storage.save_file(Path("icon.png"), b"data")
        storage.save_file(Path("image.jpg"), b"data")

        result = storage.find_file_by_pattern(Path("."), "icon")

        assert result is not None
        assert result.name == "icon.png"

    def test_find_file_by_pattern_not_found(self, storage):
        result = storage.find_file_by_pattern(Path("."), "nonexistent")

        assert result is None

    def test_list_files(self, storage, tmp_path):
        storage.save_file(Path("file1.txt"), b"data")
        storage.save_file(Path("file2.txt"), b"data")
        storage.save_file(Path("subdir/file3.txt"), b"data")

        files = storage.list_files(Path("."))

        assert len(files) == 2
        assert any(f.name == "file1.txt" for f in files)
        assert any(f.name == "file2.txt" for f in files)

    def test_list_files_empty_directory(self, storage, tmp_path):
        files = storage.list_files(Path("."))

        assert files == []

    def test_copy_file(self, storage, tmp_path):
        src = Path("source.txt")
        dst = Path("dest.txt")
        content = b"Copy me"
        storage.save_file(src, content)

        storage.copy_file(src, dst)

        assert (tmp_path / dst).exists()
        assert (tmp_path / dst).read_bytes() == content

    def test_copy_file_to_nested_destination(self, storage, tmp_path):
        src = Path("source.txt")
        dst = Path("dir1/dir2/dest.txt")
        content = b"Copy to nested"
        storage.save_file(src, content)

        storage.copy_file(src, dst)

        assert (tmp_path / dst).exists()
        assert (tmp_path / dst).read_bytes() == content

    def test_create_temp_directory(self, storage):
        temp_dir = storage.create_temp_directory()

        assert temp_dir.exists()
        assert temp_dir.is_dir()

        # Очищаем после теста
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_absolute_path(self, storage, tmp_path):
        relative_path = Path("some/file.txt")
        absolute_path = storage.get_absolute_path(relative_path)

        assert absolute_path == tmp_path / relative_path

    def test_get_absolute_path_already_absolute(self, storage):
        absolute = Path("/absolute/path")

        result = storage.get_absolute_path(absolute)

        assert result == absolute

    def test_delete_directory(self, storage, tmp_path):
        path = Path("dir_to_delete")
        storage.create_directory(path)
        storage.save_file(path / "file.txt", b"data")

        storage.delete_directory(path)

        assert not (tmp_path / path).exists()

    def test_delete_directory_not_exists(self, storage):
        path = Path("not_exists")

        storage.delete_directory(path)


class TestStorageFactories:
    def test_get_courses_resource_storage_returns_storage(self):
        storage = get_courses_resource_storage()

        assert isinstance(storage, LocalFileSystemStorage)
        assert storage.base_directory.name == "resources"

    def test_get_users_resource_storage_returns_storage(self):
        storage = get_users_resource_storage()

        assert isinstance(storage, LocalFileSystemStorage)
        assert storage.base_directory.name == "resources"
