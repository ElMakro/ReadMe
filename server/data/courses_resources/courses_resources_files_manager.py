from pathlib import Path

from server.app.api.v1.exceptions import ObjectMissingError
from server.data.courses_resources import COURSES_RESOURCES_DIRECTORY


class CoursesResourceFilesManager:
    @staticmethod
    async def get_resource_filepath(
            resource_filename: str,
    ) -> Path:
        file_path = COURSES_RESOURCES_DIRECTORY / resource_filename
        if not file_path.exists():
            raise ObjectMissingError(
                "Запрашиваемый файл не найден!",
            )

        return file_path

    @staticmethod
    async def delete_resource_file(
            resource_filename: str,
    ) -> None:
        file_path = COURSES_RESOURCES_DIRECTORY / resource_filename
        file_path.unlink(
            missing_ok=True,
        )
