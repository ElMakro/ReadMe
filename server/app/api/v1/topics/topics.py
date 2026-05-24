import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel

from server.app.api.v1.common_schemas import TimestampsMixin
from server.app.api.v1.sections.sections import SectionIDMixin


class TopicIDMixin(
    BaseModel,
):
    """Универсальная схема для необязательного поля уникального идентификатора темы курса"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: uuid.UUID = Field(
        description="Уникальный идентификатор темы",
        examples=[uuid.uuid4()],
    )


class TopicBase(
    BaseModel,
):
    """Базовая схема темы курса"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )
    section_id: uuid.UUID = Field(
        ...,
        description="Уникальный идентификатор раздела, к которому относится тема",
        examples=[uuid.uuid4()],
    )
    name: str = Field(
        ...,
        description="Название темы",
        min_length=1,
        max_length=255,
        examples=["Название темы"],
    )
    order_number: int = Field(
        ...,
        description="Порядковый номер темы в разделе (нумерация с 1)",
        ge=0,
        examples=[1],
    )
    tags: list[str] = Field(
        [],
        description="Теги объекта",
        examples=["Тег1"]
    )


class TopicCreation(
    TopicBase,
):
    """Схема запроса на создание темы"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )


class TopicUpdate(
    BaseModel,
):
    """Схема запроса на обновление темы (все поля опциональны)"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    name: str | None = Field(
        None,
        description="Название темы",
        min_length=1,
        max_length=255,
        examples=["Название темы"],
    )
    tags: list[str] = Field(
        None,
        description="Теги объекта",
        examples=["Тег1"]
    )


class TopicResponse(
    TopicBase,
    TopicIDMixin,
    SectionIDMixin,
    TimestampsMixin,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    course_id: uuid.UUID = Field(
        ...,
        description="Уникальный идентификатор курса, к которому относится тема",
        examples=[uuid.uuid4()],
    )


class TopicsFullListResponse(
    RootModel[list[TopicResponse]],
):
    """Полный список тем"""


class TopicBlockRawContent(
    BaseModel,
):
    """Модель строкового представления блока контента в теме"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    type: Literal["markdown", "uml", "latex"] = Field(
        ...,
        description="Тип контента в блоке",
        examples=["latex"],
    )
    raw_content: str = Field(
        ...,
        description="Строковое представление контента в блоке",
        examples=[r"E \equals mc^2"],
    )


class TopicRawContent(
    RootModel[list[TopicBlockRawContent]],
):
    """Модель строкового представления контента в теме"""


class TopicBlockRenderedContent(
    BaseModel,
):
    """Модель блока готового к отображению контента в теме"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    type: Literal["markdown", "latex", "file"] = Field(
        ...,
        description="Тип контента в блоке",
        examples=["latex"],
    )
    rendered_content: str = Field(
        ...,
        description="Представление контента в блоке",
        examples=["..."],
    )


class TopicRenderedContent(
    RootModel[list[TopicBlockRenderedContent]],
):
    """Модель готового к отображению контента в теме"""


class BlockCompilationError(
    BaseModel,
):
    """Модель представления ошибки компиляции блока контента"""

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    block_index: int = Field(
        ...,
        description="Порядковый номер блока в теме (начиная с 1)",
        examples=[1],
    )
    error: str = Field(
        ...,
        description="Текстовое описание ошибки",
        examples=["error"],
    )


class ContentCompilationError(
    RootModel[list[BlockCompilationError]],
):
    pass
