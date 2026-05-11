import uuid

from pydantic import BaseModel, ConfigDict, Field

from server.schemas.common import TimestampsMixin


class SectionIDMixin(BaseModel):
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
    order_number: int | None = Field(
        None,
        description="Порядковый номер",
        ge=0,
        examples=[1],
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


class SectionsListResponse(
    BaseModel,
):
    """Список ID разделов курса"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    section_ids: list[uuid.UUID] = Field(
        ...,
        description="Список уникальных идентификаторов разделов",
        examples=[[uuid.uuid4()]],
    )
    total: int = Field(
        ...,
        ge=0,
        description="Количество разделов",
        examples=[1],
    )


class SectionsFullListResponse(
    BaseModel,
):
    """Полный список разделов курса"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    sections: list[SectionResponse]
    total: int = Field(
        ...,
        ge=0,
        description="Количество разделов",
        examples=[1],
    )
