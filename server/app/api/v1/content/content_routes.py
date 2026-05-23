import uuid
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from server.app.api.openapi_docs import openapi_extra_authorization_cookie
from server.app.api.v1.common_schemas import UNPROCESSABLE_ENTITY_ERROR_TEXT
from server.app.api.v1.content.content_service import ContentService
from server.app.api.v1.courses.courses_manager import ObjectExistenceError
from server.app.api.v1.courses.courses_service import OperationPermissionError
from server.app.api.v1.users.users import UserVerification
from server.app.common_dependencies.depends import get_current_user
from server.data.data_manager import UnsupportedMediaTypeError

content_router = APIRouter(
    prefix="/content",
    tags=["Получение файлов"],
)


@content_router.get(
    "/get-topic-file",
    description="Получить файл из некоторой темы",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_403_FORBIDDEN             : {
            "description": "У пользователя нет права доступа к этому файлу",
        },
        status.HTTP_404_NOT_FOUND             : {
            "description": "Тема или файл не найдены!",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT : {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie,
)
async def get_topic_file(
        user: Annotated[UserVerification | None, Depends(
            get_current_user,
        )],
        topic_id: UUID = Query(
            ...,
            description="Идентификатор темы",
            examples=[uuid.uuid4()],
        ),
        file_name: str = Query(
            ...,
            description="Имя запрашиваемого файла",
            examples=["example.png"],
        ),
        content_service: ContentService = Depends(
            ContentService,
        ),
) -> FileResponse:
    try:
        return await content_service.get_topic_file(
            user,
            topic_id,
            file_name,
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
    except UnsupportedMediaTypeError as error:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(
                error,
            ),
        )
