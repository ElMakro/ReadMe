import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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


class TopicCreation(
    TopicBase,
):
    """Схема запроса на создание темы"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    section_id: uuid.UUID = Field(
        ...,
        description="Уникальный идентификатор раздела, к которому относится тема",
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
    order_number: int | None = Field(
        None,
        description="Порядковый номер (нумерация с 1)",
        ge=0,
        examples=[1],
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


class TopicsListResponse(
    BaseModel,
):
    """Список идентификаторов тем"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    topic_ids: list[uuid.UUID] = Field(
        ...,
        description="Список ID тем",
        examples=[[uuid.uuid4()]],
    )
    total: int = Field(
        ...,
        ge=0,
        description="Количество тем",
        examples=[1],
    )


class TopicsFullListResponse(
    BaseModel,
):
    """Полный список тем"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    topics: list[TopicResponse]
    total: int = Field(
        ...,
        ge=0,
        description="Количество тем",
        examples=[1],
    )


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
    BaseModel,
):
    """Модель строкового представления контента в теме"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    blocks: list[TopicBlockRawContent] = Field(
        ...,
        description="Упорядоченные блоки темы",
    )


class TopicBlockRenderedContent(
    BaseModel,
):
    """Модель блока готового к отображению контента в теме"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    type: Literal["markdown", "uml", "latex"] = Field(
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
    BaseModel,
):
    """Модель готового к отображению контента в теме"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    blocks: list[TopicBlockRenderedContent] = Field(
        ...,
        description="Упорядоченные блоки темы",
    )
