from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Path, UploadFile, status
from fastapi.responses import FileResponse

from server.app.api.openapi_docs import openapi_extra_authorization_cookie
from server.app.api.v1.common_schemas import UNPROCESSABLE_ENTITY_ERROR_TEXT
from server.app.api.v1.exceptions_handlers import HANDLED_EXCEPTIONS, handle_exception_chain
from server.app.api.v1.topics.topics import (
    ContentCompilationError,
    FileItem,
    TopicCreation,
    TopicIDMixin,
    TopicResponse,
    TopicsFullListResponse,
    TopicUpdate,
)
from server.app.api.v1.topics.topics_service import (
    TopicsService,
)
from server.app.api.v1.users.users import UserVerification
from server.app.common_dependencies.depends import get_auth_user, get_current_user

topics_router = APIRouter(
    prefix="/topics",
    tags=["Взаимодействие с темами курсов"],
)


@topics_router.post(
    "/create-topic",
    summary="Создать новую тему",
    response_description="Новая тема успешно создана",
    status_code=status.HTTP_201_CREATED,
    response_model=TopicIDMixin,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Ошибка компиляции контента",
            "model": ContentCompilationError,
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "У пользователя нет прав на создание темы в данном разделе",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Раздела с таким идентификатором не существует",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Тема с таким порядковым номером уже существует в этом разделе",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def create_topic(
        user: Annotated[UserVerification, Depends(get_auth_user)],
        topic_creation: TopicCreation,
        topics_service: TopicsService = Depends(TopicsService),
) -> TopicIDMixin:
    """
    Создать новую тему в разделе.
    Порядковый номер определяет отображение тем в разделе.
    """
    try:
        return await topics_service.create_topic(
            user,
            topic_creation.section_id,
            topic_creation.name,
            topic_creation.order_number,
            topic_creation.tags,
            topic_creation.raw_content,
        )
    except HANDLED_EXCEPTIONS as error:
        raise handle_exception_chain(error)


@topics_router.post(
    path="/upload-resource/{topic_id}/{block_number}/{file_number}",
    summary="Загрузить ресурс темы",
    response_description="Ресурс темы успешно загружен",
    response_model=FileItem,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Тип блока не позволяет содержать файлы",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "У пользователя нет прав на создание темы в данном разделе",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Раздела с таким идентификатором не существует, блока с таким номером не "
                           "существует или файла с таким номером не существует",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Название файла не совпадает с заявленным в теме",
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def upload_resource(
        user: Annotated[UserVerification, Depends(get_auth_user)],
        topic_id: UUID = Path(..., description="Уникальный идентификатор темы"),
        block_number: int = Path(..., description="Порядковый номер блока в теме"),
        file_number: int = Path(..., description="Порядковый номер файла в блоке"),
        resource: UploadFile = File(..., description="Ресурс темы"),
        topics_service: TopicsService = Depends(TopicsService)
) -> FileItem:
    try:
        return await topics_service.upload_resource(user, topic_id, block_number, file_number, resource)
    except HANDLED_EXCEPTIONS as error:
        raise handle_exception_chain(error)


@topics_router.get(
    "/get-resource/{topic_id}/{resource_filename}",
    description="Получить ресурс курса",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "У пользователя нет права доступа к этому файлу",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Файл не найден!",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def get_topic_resource(
        user: Annotated[UserVerification | None, Depends(
            get_current_user,
        )],
        topic_id: UUID = Path(
            ...,
            description="Уникальный идентификатор темы"
        ),
        resource_filename: str = Path(
            ...,
            description="Имя запрашиваемого файла",
            examples=["example.png"],
        ),
        topics_service: TopicsService = Depends(
            TopicsService,
        ),
) -> FileResponse:
    try:
        return FileResponse(
            await topics_service.get_resource(
                user,
                topic_id,
                resource_filename,
            ),
        )
    except HANDLED_EXCEPTIONS as error:
        raise handle_exception_chain(error)


@topics_router.get(
    "/by-section/{section_id}",
    summary="Получить список тем по уникальному идентификатору раздела",
    response_description="Список тем раздела",
    status_code=status.HTTP_200_OK,
    response_model=TopicsFullListResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Пользователь не имеет прав на просмотр тем этого раздела",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Раздела с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def get_topics_by_section(
        user: Annotated[UserVerification | None, Depends(
            get_current_user,
        )],
        section_id: UUID = Path(
            ...,
            description="Уникальный идентификатор раздела",
        ),
        topics_service: TopicsService = Depends(
            TopicsService,
        ),
) -> TopicsFullListResponse:
    """
    Получить все темы раздела, отсортированные по порядковому номеру.
    """
    try:
        return await topics_service.get_topics_by_section_id(
            user,
            section_id,
        )
    except HANDLED_EXCEPTIONS as error:
        raise handle_exception_chain(error)


@topics_router.get(
    "/by-course/{course_id}",
    summary="Получить все темы по идентификатору курса",
    response_description="Список всех тем курса",
    status_code=status.HTTP_200_OK,
    response_model=TopicsFullListResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Пользователь не имеет прав на просмотр тем этого курса",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Курса с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def get_topics_by_course(
        user: Annotated[UserVerification | None, Depends(
            get_current_user,
        )],
        course_id: UUID = Path(
            ...,
            description="Уникальный идентификатор курса",
        ),
        topics_service: TopicsService = Depends(
            TopicsService,
        ),
) -> TopicsFullListResponse:
    """
    Получить все темы курса.
    """
    try:
        return await topics_service.get_topics_by_course_id(
            user,
            course_id,
        )
    except HANDLED_EXCEPTIONS as error:
        raise handle_exception_chain(error)


@topics_router.get(
    "/{topic_id}",
    summary="Получить тему по её уникальному идентификатору",
    response_description="Тема успешно найдена",
    status_code=status.HTTP_200_OK,
    response_model=TopicResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Пользователь не имеет прав на просмотр данной темы",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Темы с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def get_topic_by_id(
        user: Annotated[UserVerification | None, Depends(
            get_current_user,
        )],
        topic_id: UUID = Path(
            ...,
            description="Уникальный идентификатор темы",
        ),
        topics_service: TopicsService = Depends(
            TopicsService,
        ),
) -> TopicResponse:
    """Получить полную информацию о теме по её идентификатору."""
    try:
        return await topics_service.get_topic_by_id(
            user,
            topic_id,
        )
    except HANDLED_EXCEPTIONS as error:
        raise handle_exception_chain(error)


@topics_router.put(
    "/{topic_id}",
    summary="Редактировать тему",
    response_description="Тема успешно отредактирована",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Ошибка компиляции контента",
            "model": ContentCompilationError,
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "У пользователя нет прав на редактирование этой темы",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Темы с таким ID не существует",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Тема с таким order_number уже существует в этом разделе",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def update_topic(
        user: Annotated[UserVerification, Depends(
            get_auth_user,
        )],
        topic_update: TopicUpdate,
        topic_id: UUID = Path(
            ...,
            description="Уникальный идентификатор темы",
        ),
        topics_service: TopicsService = Depends(
            TopicsService,
        ),
) -> None:
    """Изменить содержимое темы."""
    try:
        await topics_service.update_topic(
            user,
            topic_id,
            topic_update.name,
            topic_update.tags,
            topic_update.raw_content,
        )
    except HANDLED_EXCEPTIONS as error:
        raise handle_exception_chain(error)


@topics_router.delete(
    "/{topic_id}",
    summary="Удалить тему",
    response_description="Тема успешно удалена",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "У пользователя нет прав на удаление этой темы",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Темы с таким ID не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def delete_topic(
        user: Annotated[UserVerification, Depends(
            get_auth_user,
        )],
        topic_id: UUID = Path(
            ...,
            description="Уникальный идентификатор темы",
        ),
        topics_service: TopicsService = Depends(
            TopicsService,
        ),
) -> None:
    """
    Удалить тему и все связанные с ней заметки студентов.
    Только преподаватель курса может удалить тему.
    """
    try:
        await topics_service.delete_topic(
            user,
            topic_id,
        )
    except HANDLED_EXCEPTIONS as error:
        raise handle_exception_chain(error)
