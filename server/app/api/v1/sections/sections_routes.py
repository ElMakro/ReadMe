from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from server.app.api.openapi_docs import (
    openapi_extra_authorization_cookie_non_required,
    openapi_extra_authorization_cookie_required,
)
from server.app.api.v1.common_schemas import UNPROCESSABLE_ENTITY_ERROR_TEXT, SwapContentOrder
from server.app.api.v1.sections.sections import (
    SectionCreation,
    SectionIDMixin,
    SectionResponse,
    SectionsFullListResponse,
    SectionUpdate,
)
from server.app.api.v1.sections.sections_service import SectionsService
from server.app.api.v1.users.users import UserVerification
from server.app.common_dependencies.depends import get_auth_user, get_current_user

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
    openapi_extra=openapi_extra_authorization_cookie_required,
)
async def create_section(
        user: Annotated[UserVerification, Depends(
            get_auth_user,
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
    return await sections_service.create_section(
        user,
        section_data.course_id,
        section_data.name,
        section_data.description,
        section_data.order_number,
        section_data.tags,
    )


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
    openapi_extra=openapi_extra_authorization_cookie_non_required,
)
async def get_sections_by_course_id(
        user: Annotated[UserVerification | None, Depends(
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
    return await sections_service.get_sections_by_course_id(
        user,
        course_id,
    )


@sections_router.put(
    "/swap",
    summary="Обменять порядковые номера между разделами",
    response_description="Порядковые номера успешно обменены",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "У пользователя нет прав на редактирование этого раздела",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Раздела с таким идентификатором не существует",
        },
        status.HTTP_409_CONFLICT             : {
            "description": "Обмен между разделами разных курсов запрещён",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie_required,
)
async def swap_sections(
        user: Annotated[UserVerification, Depends(
            get_auth_user,
        )],
        sections_swap: SwapContentOrder,
        sections_service: SectionsService = Depends(
            SectionsService,
        ),
) -> None:
    """Обменять порядковые номера между разделами."""
    await sections_service.swap_sections(
        user,
        sections_swap.first_element_id,
        sections_swap.second_element_id,
    )


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
    openapi_extra=openapi_extra_authorization_cookie_non_required,
)
async def get_section_by_id(
        user: Annotated[UserVerification | None, Depends(
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
    return await sections_service.get_section_by_id(
        user,
        section_id,
    )


@sections_router.put(
    "/{section_id}",
    summary="Обновить данные о разделе",
    response_description="Данные раздела успешно обновлены",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "У пользователя нет прав на редактирование этого раздела",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Раздела с таким ID не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie_required,
)
async def update_section(
        user: Annotated[UserVerification, Depends(
            get_auth_user,
        )],
        section_update: SectionUpdate,
        section_id: UUID = Path(
            ...,
            description="Уникальный идентификатор раздела",
        ),
        sections_service: SectionsService = Depends(
            SectionsService,
        ),
) -> None:
    """Обновить информацию о разделе."""
    await sections_service.update_section(
        user,
        section_id,
        section_update.name,
        section_update.description,
        section_update.tags,
    )


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
    openapi_extra=openapi_extra_authorization_cookie_required,
)
async def delete_section(
        user: Annotated[UserVerification, Depends(
            get_auth_user,
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
    await sections_service.delete_section(
        user,
        section_id,
    )
