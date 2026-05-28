from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from server.app.api.openapi_docs import openapi_extra_authorization_cookie
from server.app.api.v1.common_schemas import UNPROCESSABLE_ENTITY_ERROR_TEXT
from server.app.api.v1.content.content_service import ContentService
from server.app.api.v1.exceptions import ObjectMissingError, OperationPermissionError
from server.app.api.v1.users.users import UserVerification
from server.app.common_dependencies.depends import get_current_user

content_router = APIRouter(
    prefix="/content",
    tags=["Получение файлов"],
)


@content_router.get(
    "/get-topic-resource",
    description="Получить ресурс курса",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_403_FORBIDDEN            : {
            "description": "У пользователя нет права доступа к этому файлу",
        },
        status.HTTP_404_NOT_FOUND            : {
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
        topic_id: UUID = Query(
            ...,
            description="Идентификатор темы",
            examples=[uuid4()],
        ),
        resource_filename: str = Query(
            ...,
            description="Имя запрашиваемого файла",
            examples=["example.png"],
        ),
        content_service: ContentService = Depends(
            ContentService,
        ),
) -> FileResponse:
    try:
        return FileResponse(
            await content_service.get_topic_resource(
                user,
                topic_id,
                resource_filename,
            ),
        )
    except OperationPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(
                error,
            ),
        )
    except ObjectMissingError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            ),
        )
