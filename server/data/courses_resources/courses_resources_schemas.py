from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from server.enums.object_type import ObjectType


class CourseResourceSchema(
    BaseModel,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    resource_filename: str = Field(
        ...,
        description="Название файла ресурса в каталоге сервера",
    )
    parent_object_id: UUID = Field(
        ...,
        description="Идентификатор родительского объекта",
    )
    parent_object_type: ObjectType = Field(
        ...,
        description="Тип родительского объекта",
    )
