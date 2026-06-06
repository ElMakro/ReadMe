import uuid
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from server.config.constants import ALLOWED_LINK_CHARACTERS

UNAUTHORIZED_ERROR_TEXT = "Пользователь не произвёл вход"
FORBIDDEN_ERROR_TEXT = "Недостаточно прав для выполнения операции"
NOT_FOUND_ERROR_TEXT = "Запрашиваемый ресурс не найден"
UNPROCESSABLE_ENTITY_ERROR_TEXT = "Ошибка валидации входных данных"
NOT_UNIQUE_FIELDS_ERROR_TEXT = "Пользователь с таким никнеймом или почтой уже существует"
NOTE_ALREADY_EXISTS_ERROR_TEXT = "Конспект к этой теме уже существует"
NOTE_FIELDS_MISMATCH_ERROR_TEXT = "Поле note_id не соответствует сочетанию полей student_id и topic_id"
NOTE_NOT_FOUND_ERROR_TEXT = "Конспект не найден или принадлежит другому пользователю"
USER_MUST_BE_IN_PROFESSORS_TABLE_ERROR_TEXT = ("Невозможно присвоить роль преподавателя: информации о пользователе "
                                               "нет в таблице преподавателей")
CANT_CHANGE_OWN_ROLE_ERROR_TEXT = "Запрещено изменять собственную роль. Обратитесь к другому администратору"
CANT_DELETE_OWN_PROFILE_ERROR_TEXT = "Запрещено удалять собственный профиль. Обратитесь к другому администратору"
APPLICATION_FIELDS_MISMATCH_ERROR_TEXT = "Поле id заявки не соответвует id пользователя"
APPLICATION_REFUSED_ERROR_TEXT = "Пользователь уже является преподавателем или его заявка уже находится на рассмотрении"
UPDATED_LINK_ERROR_TEXT = (f"Ссылка содержит недопустимые символы или имеет недопустимую длину; "
                           f"ориентируйтесь на регулярное выражение: {ALLOWED_LINK_CHARACTERS}")
WRONG_APPLICATION_LINK_ERROR_TEXT = "Неверный адрес, уточните ссылку для подачи заявки у администратора"
NOT_EXISTING_LINK_ERROR_TEXT = "Секретная часть ссылки не задана"


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
        Literal[6, 9, 15, 30],
        BeforeValidator(
            convert_to_int,
        ),
    ] = Query(
        description="Количество записей на странице",
        default=9,
    )


class SwapContentOrder(
    BaseModel,
):
    """Схема запроса на обмен порядковыми номерами элементов объектов системы"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    first_element_id: UUID = Field(
        ...,
        description="Идентификатор первого элемента",
        examples=[uuid.uuid4()],
    )
    second_element_id: UUID = Field(
        ...,
        description="Идентификатор второго элемента",
        examples=[uuid.uuid4()],
    )
