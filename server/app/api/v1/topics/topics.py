import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

from server.app.api.v1.common_schemas import TimestampsMixin
from server.app.api.v1.sections.sections import SectionIDMixin


class FileItem(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    original_filename: str = Field(..., description="Изначальное название файла")
    server_filename: str | None = Field(None, description="Имя файла на сервере")


class TopicContentBlock(
    BaseModel,
):
    """Модель блока контента в темы"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    type: Literal["markdown", "plantuml", "latex", "image", "files"] = Field(
        ...,
        description="Тип контента в блоке",
        examples=["latex"],
    )
    content: list[str] | list[FileItem] = Field(
        ...,
        description="Представление контента в блоке",
    )

    @model_validator(mode="after")
    def validate_content_to_type(self):
        if self.type == "files":
            if not all(isinstance(item, FileItem) for item in self.content):
                if all(isinstance(item, dict) for item in self.content):
                    converted_content = []
                    for item in self.content:
                        converted_content.append(FileItem(
                            original_filename=item.get("original_name") or item.get("original_filename"),
                            server_filename=item.get("server_name") or item.get("server_filename")
                        ))
                    self.content = converted_content
                else:
                    raise ValueError("Для блока files content должен содержать FileItem объекты")

            for item in self.content:
                if not item.original_filename:
                    raise ValueError("Каждый FileItem в блоке files должен иметь original_name")

        elif self.type in ["markdown", "plantuml", "latex", "image"]:
            if not all(isinstance(item, str) for item in self.content):
                raise ValueError(f"Для блока {self.type} content должен содержать строки")

            if len(self.content) != 1:
                raise ValueError(f"Для блока {self.type} ожидается ровно один элемент в content")

        return self


class TopicContent(
    RootModel[list[TopicContentBlock]],
):
    """Модель контента темы"""


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
        examples=[["Тег1"]],
    )
    raw_content: TopicContent = Field(
        default_factory=list,
        description="Текстовое представление контента в теме",
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

    name: str = Field(
        None,
        description="Название темы",
        min_length=1,
        max_length=255,
        examples=["Название темы"],
    )
    tags: list[str] = Field(
        None,
        description="Теги объекта",
        examples=[["Тег1"]],
    )
    raw_content: TopicContent = Field(
        ...,
        description="Текстовое представление контента в теме",
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
    rendered_content: TopicContent = Field(
        default_factory=list,
        description="Представление готового к отображению контента темы",
    )
    topic_directory_path: str = Field(
        ...,
        description="Расположение директории темы на сервере",
        examples=["/"],
    )


class TopicsFullListResponse(
    RootModel[list[TopicResponse]],
):
    """Полный список тем"""


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
