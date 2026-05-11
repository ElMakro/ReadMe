from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from server.app.service.courses_service import CoursesService
from server.schemas.common import UNPROCESSABLE_ENTITY_ERROR_TEXT, PaginationParameters
from server.schemas.courses import (
    CourseChangeOwner,
    CourseCreation,
    CourseFullListResponse,
    CourseIDMixin,
    CourseResponse,
)

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
)
async def create_course(
        course_data: CourseCreation,
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
) -> CourseIDMixin:
    """
    Создать новый курс.
    Текущий пользователь автоматически становится преподавателем курса.
    """
    pass


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
)
async def get_course_by_id(
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
)
async def search_courses_by_name(
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
    "/followed-courses",
    summary="Получить курсы, на которых обучается текущий пользователь",
    response_description="Список курсов, на которых обучается пользователь",
    status_code=status.HTTP_200_OK,
    response_model=CourseFullListResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
)
async def get_followed_courses(
        pagination_parameters: PaginationParameters = Depends(),
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
) -> CourseFullListResponse:
    """
    Получить пагинированный список курсов, на которых обучается текущий пользователь.
    """
    pass


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
)
async def get_controlled_courses(
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
    status_code=status.HTTP_200_OK,
    response_model=CourseResponse,
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
)
async def update_course(
        course_id: UUID = Path(
            ...,
            description="Уникальный идентификатор курса",
        ),
        courses_service: CoursesService = Depends(
            CoursesService,
        ),
) -> CourseResponse:
    """Обновить информацию о курсе (только для преподавателя курса ил администратора системы)."""
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
)
async def change_course_owner(
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
            "description": "Курса с таким ID не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
)
async def delete_course(
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
