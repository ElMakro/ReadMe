from uuid import UUID

from fastapi import Depends
from sqlalchemy.exc import IntegrityError

from server.app.api.v1.exceptions import ObjectMissingError
from server.config.db_dependency import DBDependency
from server.data.courses_resources.courses_resources_schemas import CourseResourceSchema
from server.database.models.courses_resources import CoursesResources
from server.enums.object_type import ObjectType


class ObjectExistenceError(
    ValueError,
):
    """Ошибка, связанная с существованием объекта в системе"""


class CoursesResourcesRelationManager:
    def __init__(
            self,
            db: DBDependency = Depends(
                DBDependency,
            ),
    ):
        self.db = db

    async def register_resource_record(
            self,
            resource_filename: str,
            parent_object_id: UUID,
            parent_object_type: ObjectType,
    ) -> None:
        async with self.db.db_session() as session:
            resource = CoursesResources(
                resource_filename=resource_filename,
                parent_object_id=parent_object_id,
                parent_object_type=parent_object_type,
            )
            try:
                session.add(
                    resource,
                )
                await session.commit()
            except IntegrityError:
                raise ObjectExistenceError(
                    "Регистрируемый ресурс уже существует!",
                )

    async def get_resource_record_by_filename(
            self,
            resource_filename: str,
    ) -> CourseResourceSchema:
        async with self.db.db_session() as session:
            resource = await session.get(
                CoursesResources,
                resource_filename,
            )

        if resource is None:
            raise ObjectMissingError(
                "Запрашиваемый ресурс не найден!",
            )

        return CourseResourceSchema.model_validate(
            resource,
        )
