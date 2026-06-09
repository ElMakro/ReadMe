from pathlib import Path
from uuid import UUID

from fastapi import Depends, UploadFile

from server.app.api.v1.exceptions import ObjectMissingError
from server.app.api.v1.users.users import CreatedUserInfo
from server.data.resource_storage import IResourceStorage, get_users_resource_storage
from server.data.users_resources.icons_generator import IconsGenerator


class UsersResourcesManager:
    def __init__(
            self,
            storage: IResourceStorage = Depends(get_users_resource_storage),
            icons_generator: IconsGenerator = Depends(IconsGenerator),
    ):
        self.storage = storage
        self.icons_generator = icons_generator

    @staticmethod
    def get_user_directory_path(user_id: UUID) -> Path:
        return Path(str(user_id))

    def get_absolute_user_directory_path(self, user_id: UUID) -> Path:
        return self.storage.get_absolute_path(self.get_user_directory_path(user_id))

    def create_user(self, created_user_info: CreatedUserInfo) -> None:
        user_dir = self.get_absolute_user_directory_path(created_user_info.id)
        self.storage.create_directory(user_dir)

        files_dir = user_dir / "files"
        self.storage.create_directory(files_dir)

        self.icons_generator.generate_icon(created_user_info, user_dir)

    def get_user_icon_path(self, user_id: UUID) -> Path:
        user_dir = self.get_user_directory_path(user_id)
        if not self.storage.file_exists(user_dir):
            raise ObjectMissingError("Пользователя с таким id не существует!")

        icon_path = self.storage.find_file_by_pattern(user_dir, "icon")
        if icon_path is None:
            raise ObjectMissingError("Иконка пользователя не найдена!")
        return icon_path

    def delete_user_icon(self, user_id: UUID) -> None:
        self.storage.delete_files_by_pattern(self.get_user_directory_path(user_id), "icon")

    async def set_user_icon(self, user_id: UUID, icon_upload_file: UploadFile) -> None:
        user_dir = self.get_user_directory_path(user_id)
        if not self.storage.file_exists(user_dir):
            raise ObjectMissingError("Пользователя с таким id не существует!")

        self.delete_user_icon(user_id)

        filename = icon_upload_file.filename
        if not filename:
            raise ValueError("Имя файла иконки не может быть пустым")

        icon_path = user_dir / f"icon{Path(filename).suffix}"

        content = await icon_upload_file.read()
        self.storage.save_file(icon_path, content)
