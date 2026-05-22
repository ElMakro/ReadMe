import uuid

from pydantic import BaseModel, ConfigDict, Field, RootModel

from server.app.api.v1.common_schemas import TimestampsMixin
from server.config.constants import MAX_COURSE_DESCRIPTION_LENGTH


class SectionIDMixin(
    BaseModel,
):
    """Универсальная схема для необязательного поля уникального идентификатора раздела курса"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: uuid.UUID = Field(
        description="Уникальный идентификатор раздела",
        examples=[uuid.uuid4()],
    )


class SectionBase(
    BaseModel,
):
    """Базовая схема раздела курса"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    name: str = Field(
        ...,
        description="Название раздела",
        min_length=1,
        max_length=255,
        examples=["Название раздела"],
    )
    
    description: str = Field(
        ...,
        description="Описание раздела",
        max_length=MAX_COURSE_DESCRIPTION_LENGTH,
        examples=["Описание раздела"],
    )
    order_number: int = Field(
        ...,
        description="Порядковый номер раздела в курсе (нумерация с 1)",
        ge=0,
        examples=[1],
    )


class SectionCreation(
    SectionBase,
):
    """Схема запроса на создание раздела"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    course_id: uuid.UUID = Field(
        ...,
        description="Уникальный идентификатор курса, к которому относится раздел",
    )


class SectionUpdate(
    BaseModel,
):
    """Схема запроса на изменение раздела (все поля опциональны)"""
    model_config = ConfigDict(
        from_attributes=True,
    )

    name: str | None = Field(
        None,
        description="Название раздела",
        min_length=1,
        max_length=255,
        examples=["Название раздела"],
    )
    description: str | None = Field(
        None,
        description="Описание раздела",
        examples=["Описание раздела"],
    )


class SectionResponse(
    SectionBase,
    SectionIDMixin,
    TimestampsMixin,
):
    """Схема ответа с полной информацией о разделе"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    course_id: uuid.UUID = Field(
        ...,
        description="Уникальный идентификатор курса",
    )


class SectionsFullListResponse(
    RootModel[list[SectionResponse]],
):
    """Список разделов курса, с полной информацией о них"""
    pass
