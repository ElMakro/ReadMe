from pathlib import Path
from uuid import UUID

from fastapi import Depends, UploadFile

from server.app.api.v1.exceptions import ObjectMissingError
from server.app.api.v1.users.users import CreatedUserInfo
from server.data.users_resources import USERS_RESOURCES_DIRECTORY_PATH
from server.data.users_resources.icons_generator import IconsGenerator


class UsersResourcesManager:
    def __init__(self, icons_generator: IconsGenerator = Depends(IconsGenerator)):
        self.icons_generator = icons_generator

    @staticmethod
    def get_user_directory_path(user_id: UUID) -> Path:
        return USERS_RESOURCES_DIRECTORY_PATH / str(user_id)

    def get_user_files_directory_path(self, user_id: UUID) -> Path:
        return self.get_user_directory_path(user_id) / "files"

    def create_user(self, created_user_info: CreatedUserInfo) -> None:
        user_directory_path = self.get_user_directory_path(created_user_info.id)
        user_directory_path.mkdir(parents=True, exist_ok=True)

        user_files_directory_path = self.get_user_files_directory_path(created_user_info.id)
        user_files_directory_path.mkdir(parents=True, exist_ok=True)

        self.icons_generator.generate_icon(created_user_info, user_directory_path)

    def get_user_icon_path(self, user_id: UUID) -> Path:
        user_directory_path = self.get_user_directory_path(user_id)
        if not user_directory_path.exists():
            raise ObjectMissingError("Пользователя с таким id не существует!")

        for filepath in user_directory_path.iterdir():
            if filepath.is_file() and "icon" in filepath.name:
                return filepath

        raise ObjectMissingError(
            "Иконка пользователя не найдена!",
        )

    def set_user_icon(self, user_id: UUID, icon_upload_file: UploadFile) -> None:
        user_directory_path = self.get_user_directory_path(user_id)
        if not user_directory_path.exists():
            raise ObjectMissingError("Пользователя с таким id не существует!")

        icon_upload_file_filename = icon_upload_file.filename
        assert icon_upload_file_filename is not None
        icon_path = user_directory_path / f"icon{Path(icon_upload_file_filename).suffix}"
        icon_file = icon_upload_file.file

        with open(icon_path, "wb") as icon_result_file:
            icon_result_file.write(icon_file.read())

        icon_file.close()
