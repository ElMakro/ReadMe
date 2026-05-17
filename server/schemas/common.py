from datetime import datetime
from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

FORBIDDEN_ERROR_TEXT = "Недостаточно прав для выполнения операции"
NOT_FOUND_ERROR_TEXT = "Запрашиваемый ресурс не найден"
UNPROCESSABLE_ENTITY_ERROR_TEXT = "Ошибка валидации входных данных"


class CreatedAtMixin:
    """Универсальная схема для необязательного поля временной отметки создания"""
    created_at: datetime = Field(
        description="Дата и время создания",
        examples=[datetime.now()],
    )


class UpdatedAtMixin:
    """Универсальная схема для необязательного поля временной отметки последнего редактирования"""
    updated_at: datetime = Field(
        description="Дата и время последнего редактирования",
        examples=[datetime.now()],
    )


class TimestampsMixin(
    CreatedAtMixin,
    UpdatedAtMixin,
):
    """Универсальная схема для комбинации необязательных временных отметок"""
    pass


class MessageResponse(
    BaseModel,
):
    """Простой текстовый ответ"""
    message: str = Field(
        ...,
        description="Сообщение",
    )
    details: dict | None = Field(
        None,
        description="Дополнительные детали",
    )


def convert_to_int(
        value,
):
    return int(
        value,
    )



class PaginationParameters(
    BaseModel,
):
    """Параметры пагинации"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    page: int = Query(
        description="Номер страницы",
        examples=[1, 2, 3],
        default=1,
    )
    records_per_page: Annotated[
        Literal[5, 10, 15, 20, 30],
        BeforeValidator(
            convert_to_int,
        ),
    ] = Query(
        description="Количество записей на странице",
        default=10,
    )
