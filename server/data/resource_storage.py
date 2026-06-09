import logging
import time
from abc import ABC, abstractmethod
from functools import wraps
from pathlib import Path
from shutil import copy2, rmtree
from tempfile import mkdtemp

from server.data.courses_resources import COURSES_RESOURCES_DIRECTORY_PATH
from server.data.users_resources import USERS_RESOURCES_DIRECTORY_PATH


def retry_io(max_retries: int = 3, delay: float = 0.5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OSError as e:
                    logging.warning(
                        f"Ошибка ввода/вывода в {func.__name__} (попытка {attempt + 1}/{max_retries}): {e}"
                    )
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay)

            logging.error("Критическая ошибка ввода/вывода: не удалось выполнить операцию")
            return func(*args, **kwargs)

        return wrapper

    return decorator


class IResourceStorage(ABC):
    @abstractmethod
    def create_directory(self, path: Path) -> None:
        pass

    @abstractmethod
    def delete_directory(self, path: Path) -> None:
        pass

    @abstractmethod
    def save_file(self, path: Path, content: bytes) -> None:
        pass

    @abstractmethod
    def delete_file(self, path: Path) -> None:
        pass

    @abstractmethod
    def file_exists(self, path: Path) -> bool:
        pass

    @abstractmethod
    def delete_files_by_pattern(self, directory: Path, pattern: str) -> None:
        pass

    @abstractmethod
    def find_file_by_pattern(self, directory: Path, pattern: str) -> Path | None:
        pass

    @abstractmethod
    def list_files(self, directory: Path) -> list[Path]:
        pass

    @abstractmethod
    def copy_file(self, src: Path, dst: Path) -> None:
        pass

    @abstractmethod
    def create_temp_directory(self) -> Path:
        pass

    @abstractmethod
    def get_absolute_path(self, path: Path) -> Path:
        pass


class LocalFileSystemStorage(IResourceStorage):
    def __init__(self, base_directory: Path):
        self.base_directory = base_directory

    def _resolve(self, path: Path) -> Path:
        return path if path.is_absolute() else self.base_directory / path

    @retry_io()
    def create_directory(self, path: Path) -> None:
        self._resolve(path).mkdir(parents=True, exist_ok=True)

    @retry_io()
    def delete_directory(self, path: Path) -> None:
        full_path = self._resolve(path)
        if full_path.exists() and full_path.is_dir():
            rmtree(full_path)

    @retry_io()
    def save_file(self, path: Path, content: bytes) -> None:
        full_path = self._resolve(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)

    @retry_io()
    def delete_file(self, path: Path) -> None:
        self._resolve(path).unlink(missing_ok=True)

    def file_exists(self, path: Path) -> bool:
        return self._resolve(path).exists()

    @retry_io()
    def delete_files_by_pattern(self, directory: Path, pattern: str) -> None:
        full_dir = self._resolve(directory)
        if not full_dir.exists():
            return
        for filepath in full_dir.iterdir():
            if filepath.is_file() and pattern in filepath.name:
                filepath.unlink()

    def find_file_by_pattern(self, directory: Path, pattern: str) -> Path | None:
        full_dir = self._resolve(directory)
        if not full_dir.exists():
            return None
        for filepath in full_dir.iterdir():
            if filepath.is_file() and pattern in filepath.name:
                return filepath
        return None

    def list_files(self, directory: Path) -> list[Path]:
        full_dir = self._resolve(directory)
        if not full_dir.exists() or not full_dir.is_dir():
            return []
        return [f for f in full_dir.iterdir() if f.is_file()]

    @retry_io()
    def copy_file(self, src: Path, dst: Path) -> None:
        full_src = self._resolve(src)
        full_dst = self._resolve(dst)
        full_dst.parent.mkdir(parents=True, exist_ok=True)
        copy2(full_src, full_dst)

    def create_temp_directory(self) -> Path:
        return Path(mkdtemp())

    def get_absolute_path(self, path: Path) -> Path:
        return self._resolve(path)


def get_courses_resource_storage() -> IResourceStorage:
    return LocalFileSystemStorage(COURSES_RESOURCES_DIRECTORY_PATH)


def get_users_resource_storage() -> IResourceStorage:
    return LocalFileSystemStorage(USERS_RESOURCES_DIRECTORY_PATH)
