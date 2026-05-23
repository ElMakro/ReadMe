from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status

from server.app.api.openapi_docs import openapi_extra_authorization_cookie
from server.app.api.v1.common_schemas import UNPROCESSABLE_ENTITY_ERROR_TEXT
from server.app.api.v1.courses.courses_manager import ObjectExistenceError
from server.app.api.v1.courses.courses_service import OperationPermissionError
from server.app.api.v1.sections.sections_service import OrderNumberConflictError
from server.app.api.v1.topics.topics import (
    ContentCompilationError,
    TopicCreation,
    TopicIDMixin,
    TopicRawContent,
    TopicRenderedContent,
    TopicResponse,
    TopicsFullListResponse,
    TopicUpdate,
)
from server.app.api.v1.topics.topics_service import TopicsService
from server.app.api.v1.users.users import UserVerification
from server.app.common_dependencies.depends import get_auth_user, get_current_user
from server.data.compilation_manager import CompilationError

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
        status.HTTP_403_FORBIDDEN            : {
            "description": "У пользователя нет прав на создание темы в данном разделе",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Раздела с таким идентификатором не существует",
        },
        status.HTTP_409_CONFLICT             : {
            "description": "Тема с таким порядковым номером уже существует в этом разделе",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def create_topic(
        user: Annotated[UserVerification, Depends(
            get_auth_user,
        )],
        topic_data: TopicCreation,
        topics_service: TopicsService = Depends(
            TopicsService,
        ),
) -> TopicIDMixin:
    """
    Создать новую тему в разделе.
    Порядковый номер определяет отображение тем в разделе.
    """
    try:
        return await topics_service.create_topic(
            user,
            topic_data.section_id,
            topic_data.name,
            topic_data.order_number,
        )
    except OperationPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(
                error,
            ),
        )
    except ObjectExistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            ),
        )
    except OrderNumberConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(
                error,
            ),
        )


@topics_router.get(
    "/by-section/{section_id}",
    summary="Получить список тем по уникальному идентификатору раздела",
    response_description="Список тем раздела",
    status_code=status.HTTP_200_OK,
    response_model=TopicsFullListResponse,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на просмотр тем этого раздела",
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
    except OperationPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(
                error,
            ),
        )
    except ObjectExistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            ),
        )


@topics_router.get(
    "/by-course/{course_id}",
    summary="Получить все темы по идентификатору курса",
    response_description="Список всех тем курса",
    status_code=status.HTTP_200_OK,
    response_model=TopicsFullListResponse,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на просмотр тем этого курса",
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
    except OperationPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(
                error,
            ),
        )
    except ObjectExistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            ),
        )


@topics_router.get(
    "/get-rendered-content/{topic_id}",
    summary="Получить готовый к отображению контент темы",
    status_code=status.HTTP_200_OK,
    response_description="Готовый к отображению контент темы успешно получен",
    response_model=TopicRenderedContent,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на просмотр контента",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Темы с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def get_rendered_content(
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
) -> TopicRenderedContent:
    try:
        return await topics_service.get_rendered_content(
            user,
            topic_id,
        )
    except OperationPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(
                error,
            ),
        )
    except ObjectExistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            ),
        )


@topics_router.get(
    "/get-raw-content/{topic_id}",
    summary="Получить строковое представление контента темы",
    status_code=status.HTTP_200_OK,
    response_description="Строковое представление контента темы успешно получено",
    response_model=TopicRawContent,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на просмотр контента",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Темы с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def get_raw_content(
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
) -> TopicRawContent:
    try:
        return await topics_service.get_raw_content(
            user,
            topic_id,
        )
    except OperationPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(
                error,
            ),
        )
    except ObjectExistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            ),
        )


@topics_router.put(
    "/put-content/{topic_id}",
    summary="Установить контент темы",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST          : {
            "description"   : "Ошибка компиляции контента",
            "model": ContentCompilationError,
        },
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на установление контента",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Темы с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def put_topic_content(
        user: Annotated[UserVerification, Depends(
            get_auth_user,
        )],
        topic_raw_content: TopicRawContent,
        topic_id: UUID = Path(
            ...,
            description="Уникальный идентификатор темы",
        ),
        topics_service: TopicsService = Depends(
            TopicsService,
        ),
):
    try:
        await topics_service.put_topic_content(
            user,
            topic_id,
            topic_raw_content,
        )
    except CompilationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[dict(element) for element in error.content_error.root],
        )
    except OperationPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(
                error,
            ),
        )
    except ObjectExistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            ),
        )


@topics_router.get(
    "/{topic_id}",
    summary="Получить тему по её уникальному идентификатору",
    response_description="Тема успешно найдена",
    status_code=status.HTTP_200_OK,
    response_model=TopicResponse,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "Пользователь не имеет прав на просмотр данной темы",
        },
        status.HTTP_404_NOT_FOUND            : {
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
    except OperationPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(
                error,
            ),
        )
    except ObjectExistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            ),
        )


@topics_router.put(
    "/{topic_id}",
    summary="Редактировать тему",
    response_description="Тема успешно отредактирована",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "У пользователя нет прав на редактирование этой темы",
        },
        status.HTTP_404_NOT_FOUND            : {
            "description": "Темы с таким ID не существует",
        },
        status.HTTP_409_CONFLICT             : {
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
        topic_id: UUID = Path(
            ...,
            description="Уникальный идентификатор темы",
        ),
        topic_update: TopicUpdate = Depends(),
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
        )
    except OperationPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(
                error,
            ),
        )
    except ObjectExistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            ),
        )


@topics_router.delete(
    "/{topic_id}",
    summary="Удалить тему",
    response_description="Тема успешно удалена",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "У пользователя нет прав на удаление этой темы",
        },
        status.HTTP_404_NOT_FOUND            : {
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
    except OperationPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(
                error,
            ),
        )
    except ObjectExistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            ),
        )
