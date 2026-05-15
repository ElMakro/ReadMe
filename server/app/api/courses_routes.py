from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from server.app.api.openapi_docs import openapi_extra_authorization_cookie
from server.app.service.courses_service import CoursesService
from server.app.service.depends import get_current_user
from server.schemas.common import UNPROCESSABLE_ENTITY_ERROR_TEXT, PaginationParameters
from server.schemas.courses import (
    CourseChangeOwner,
    CourseCreation,
    CourseFullListResponse,
    CourseIDMixin,
    CourseResponse,
    CoursesList,
    CourseUpdate,
)
from server.schemas.users import UserVerification

courses_router = APIRouter(
    prefix="/courses",
    tags=["Взаимодействие с курсами"],
)


@courses_router.post(
    "/create-course",
    summary="Создать новый курс",
    response_description="Новый курс успешно создан",
    status_code=status.HTTP_201_CREATED,
    response_model=CourseIDMixin,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на создание курса",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def create_course(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        course_data: CourseCreation,
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
) -> CourseIDMixin:
    """
    Создать новый курс.
    Текущий пользователь автоматически становится преподавателем курса.
    """
    return await courses_service.create_course(
        user,
        course_data.name,
        course_data.description,
        course_data.is_public,
        course_data.is_content_public,
    )


@courses_router.get(
    "/{course_id}",
    summary="Получить курс по его идентификатору",
    response_description="Курс успешно найден",
    status_code=status.HTTP_200_OK,
    response_model=CourseResponse,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на просмотр данного курса",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Курса с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def get_course_by_id(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        course_id: UUID = Path(
            ...,
            description="Уникальный идентификатор курса",
        ),
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
) -> CourseResponse:
    """Получить полную информацию о курсе по его идентификатору."""
    pass


@courses_router.get(
    "/search/{course_name_part}",
    summary="Поиск курсов по названию",
    response_description="Список курсов, соответствующих критериям поиска",
    status_code=status.HTTP_200_OK,
    response_model=CourseFullListResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def search_courses_by_name(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        pagination_parameters: PaginationParameters = Depends(),
        course_name_part: str = Path(
            ...,
            description="Часть названия курса, по которой происходит поиск",
            examples=["Назван"],
        ),
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
) -> CourseFullListResponse:
    """
    Пагинированный поиск курсов по части названия.
    Возвращает курсы, в названии которых содержится указанная подстрока.
    """
    pass


@courses_router.get(
    path="/followed-courses",
    response_model=CoursesList,
    status_code=status.HTTP_200_OK,
    response_description="Курсы пользователя получены",
    responses={
        status.HTTP_401_UNAUTHORIZED         : {
            "description": "Пользователь не произвёл вход",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Некорректно переданы параметры",
        },
    },
)
async def get_followed_courses(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        pagination_parameters: PaginationParameters = Depends(),
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
) -> CoursesList:
    """
    Получить пагинированный список курсов, на которых обучается текущий пользователь.
    """
    result = await courses_service.get_courses_for_user(
        user=user,
        page=pagination_parameters.page,
        size=pagination_parameters.records_per_page,
    )
    return result


@courses_router.get(
    "/controlled-courses",
    summary="Получить курсы, на которых преподаёт текущий пользователь",
    response_description="Список курсов, на которых преподаёт пользователь",
    status_code=status.HTTP_200_OK,
    response_model=CourseFullListResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def get_controlled_courses(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        pagination_parameters: PaginationParameters = Depends(),
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
) -> CourseFullListResponse:
    """
    Получить пагинированный список курсов, на которых преподаёт текущий пользователь.
    """
    pass


@courses_router.put(
    "/{course_id}",
    summary="Обновить данные о курсе",
    response_description="Данные курса успешно обновлены",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на редактирование курса",
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
async def update_course(
        course_update: CourseUpdate,
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        course_id: UUID = Path(
            ...,
            description="Уникальный идентификатор курса",
        ),
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
):
    """Обновить информацию о курсе (только для преподавателя курса или администратора системы)."""
    pass


@courses_router.put(
    "/{course_id}/change_owner",
    summary="Сменить владельца курса",
    response_description="Владелец курса успешно изменён",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на смену владельца курса",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Курс или новый преподаватель не найдены",
        },
        status.HTTP_409_CONFLICT             : {
            "description": "Новый владелец уже является преподавателем этого курса",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def change_course_owner(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        owner_data: CourseChangeOwner,
        course_id: UUID = Path(
            ...,
            description="Уникальный идентификатор курса",
        ),
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
) -> None:
    """
    Сменить преподавателя курса.
    Только текущий преподаватель или администратор может передать права другому пользователю.
    """
    pass


@courses_router.delete(
    "/{course_id}",
    summary="Удалить курс",
    response_description="Курс успешно удалён",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на удаление курса",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Курса с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def delete_course(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        course_id: UUID = Path(
            ...,
            description="Уникальный идентификатор курса",
        ),
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
) -> None:
    """
    Удалить курс и все связанные с ним данные (разделы, темы, заметки студентов).
    Только преподаватель курса или администратор системы могут его удалить.
    """
    pass


@courses_router.put(
    "/put-content/{course_id}",
    summary="Установить контент оглавления курса",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на установление контента",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Курса с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    deprecated=True,
    openapi_extra=openapi_extra_authorization_cookie,
)
async def put_course_content(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        course_id: UUID = Path(
            ...,
            description="Уникальный идентификатор курса",
        ),
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
):
    pass


@courses_router.post(
    "/enroll/{course_id}",
    summary="Записаться на курс",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Текущий пользователь успешно записан на курс",
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на запись на данный курс",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Курса с таким идентификатором не существует",
        },
        status.HTTP_409_CONFLICT             : {
            "description": "Пользователь уже записан на данный курс",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def self_enroll_on_course(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        course_id: UUID = Path(
            ...,
            description="Уникальный идентификатор курса",
        ),
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
):
    """Записать текущего пользователя на курс"""
    pass


@courses_router.post(
    "/unenroll/{course_id}",
    summary="Отписаться от курса",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Текущий пользователь успешно отписан от курса",
    responses={
        status.HTTP_404_NOT_FOUND            : {
            "description": "Курса с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def self_unenroll_from_course(
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        course_id: UUID = Path(
            ...,
            description="Уникальный идентификатор курса",
        ),
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
):
    """Отписать текущего пользователя от курса"""
    pass
