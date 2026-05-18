from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from server.app.api.openapi_docs import openapi_extra_authorization_cookie
from server.app.api.v1.common_schemas import UNPROCESSABLE_ENTITY_ERROR_TEXT
from server.app.api.v1.sections.sections import (
    SectionCreation,
    SectionIDMixin,
    SectionResponse,
    SectionsFullListResponse,
    SectionsListResponse,
    SectionUpdate,
)
from server.app.api.v1.sections.sections_service import SectionsService
from server.app.api.v1.users.users import UserVerification
from server.app.common_dependencies.depends import get_current_user

sections_router = APIRouter(
    prefix="/sections",
    tags=["Взаимодействие с разделами курсов"],
)


@sections_router.post(
    "/create-section",
    summary="Создать новый раздел",
    response_description="Новый раздел успешно создан",
    status_code=status.HTTP_201_CREATED,
    response_model=SectionIDMixin,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "У пользователя нет прав на создание раздела в данном курсе",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Курса с таким идентификатором не существует",
        },
        status.HTTP_409_CONFLICT             : {
            "description": "Раздел с таким порядковым номером уже существует в этом курсе",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def create_section(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        section_data: SectionCreation,
        sections_service: SectionsService = Depends(
            SectionsService,
        ),
) -> SectionIDMixin:
    """
    Создать новый раздел в курсе.
    Порядковый номер определяет отображение разделов.
    """
    pass


@sections_router.get(
    "/{section_id}",
    summary="Получить информацию о разделе по его идентификатору",
    response_description="Раздел успешно найден",
    status_code=status.HTTP_200_OK,
    response_model=SectionResponse,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на просмотр данного раздела",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Раздела с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def get_section_by_id(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        section_id: UUID = Path(
            ...,
            description="Уникальный идентификатор раздела",
        ),
        sections_service: SectionsService = Depends(
            SectionsService,
        ),
) -> SectionResponse:
    """Получить полную информацию о разделе по его идентификатору."""
    pass


@sections_router.get(
    "/by_course/{course_id}",
    summary="Получить список разделов по идентификатору курса",
    response_description="Список разделов курса",
    status_code=status.HTTP_200_OK,
    response_model=SectionsFullListResponse,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на просмотр разделов этого курса",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Курса с таким ID не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def get_sections_by_course(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        course_id: UUID = Path(
            ...,
            description="Уникальный идентификатор курса",
        ),
        sections_service: SectionsService = Depends(
            SectionsService,
        ),
) -> SectionsFullListResponse:
    """
    Получить все разделы курса, отсортированные по порядковому номеру.
    Возвращает полные данные о разделах.
    """
    pass


@sections_router.get(
    "/by_course/{course_id}/ids",
    summary="Получить список ID разделов по ID курса",
    response_description="Список ID разделов курса",
    status_code=status.HTTP_200_OK,
    response_model=SectionsListResponse,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на просмотр разделов этого курса",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Курса с таким ID не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def get_section_ids_by_course(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        course_id: UUID = Path(
            ...,
            description="Уникальный идентификатор курса",
        ),
        sections_service: SectionsService = Depends(
            SectionsService,
        ),
) -> SectionsListResponse:
    """
    Получить только ID разделов курса, отсортированные по порядковому номеру.
    Полезно для получения списка ID для дальнейших запросов.
    """
    pass


@sections_router.put(
    "/{section_id}",
    summary="Обновить данные о разделе",
    response_description="Данные раздела успешно обновлены",
    status_code=status.HTTP_200_OK,
    response_model=SectionResponse,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "У пользователя нет прав на редактирование этого раздела",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Раздела с таким ID не существует",
        },
        status.HTTP_409_CONFLICT             : {
            "description": "Раздел с таким order_number уже существует в этом курсе",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def update_section(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        section_data: SectionUpdate,
        section_id: UUID = Path(
            ...,
            description="Уникальный идентификатор раздела",
        ),
        sections_service: SectionsService = Depends(
            SectionsService,
        ),
) -> SectionResponse:
    """Обновить информацию о разделе."""
    pass


@sections_router.delete(
    "/{section_id}",
    summary="Удалить раздел",
    response_description="Раздел успешно удалён",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "У пользователя нет прав на удаление этого раздела",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Раздела с таким ID не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def delete_section(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        section_id: UUID = Path(
            ...,
            description="Уникальный идентификатор раздела",
        ),
        sections_service: SectionsService = Depends(
            SectionsService,
        ),
) -> None:
    """
    Удалить раздел и все связанные с ним темы.
    Только преподаватель курса может удалить раздел.
    """
    pass


@sections_router.put(
    "/put-content/{section_id}",
    summary="Установить контент оглавления раздела",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на установление контента",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Раздела с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    deprecated=True,
    openapi_extra=openapi_extra_authorization_cookie,
)
async def put_section_content(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        section_id: UUID = Path(
            ...,
            description="Уникальный идентификатор раздела",
        ),
        sections_service: SectionsService = Depends(
            SectionsService,
        ),
):
    pass
