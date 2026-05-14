from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from server.app.api.openapi_docs import openapi_extra_authorization_cookie
from server.app.service.depends import get_current_user
from server.app.service.users_service import UsersService
from server.schemas.common import MessageResponse
from server.schemas.users import CreatedUserInfo, UserAuthentication, UserRegistration, UserVerification

auth_router = APIRouter(
    prefix="/auth",
    tags=["Регистрация и авторизация пользователей"],
)


@auth_router.post(
    path="/reg",
    response_model=CreatedUserInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя в системе",
)
async def registration(
        user: UserRegistration,
        user_service: UsersService = Depends(
            UsersService,
        ),
) -> CreatedUserInfo:
    """Создаёт пользователя в системе"""
    return await user_service.register_user(
        user=user,
    )


@auth_router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    summary="Идентификация и аутентификация пользователя в системе",
    response_model=MessageResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Успешный вход в систему",
            "headers"    : {
                "Set-Cookie": {
                    "description": "Устанавливает cookie Authorization с зашифрованным JWT токеном",
                    "schema"     : {
                        "type"   : "string",
                        "example": "Authorization=...;",
                    },
                },
            },
        },
    },
)
async def login(
        user: UserAuthentication,
        response: Response,
        user_service: UsersService = Depends(
            UsersService,
        ),
) -> MessageResponse:
    """Идентифицирует и аутентифицирует пользователя. В случае корректности пользовательских данных кладёт
    авторизационный cookie Authorization с зашифрованным JWT токеном."""
    return await user_service.login_user(
        user=user,
        response=response,
    )


@auth_router.get(
    path="/logout",
    status_code=status.HTTP_200_OK,
    summary="Выход пользователя из системы",
    response_model=MessageResponse,
    openapi_extra=openapi_extra_authorization_cookie,
)
async def logout(
        response: Response,
        user: Annotated[UserVerification, Depends(
            get_current_user,
        )],
        user_service: UsersService = Depends(
            UsersService,
        ),
) -> MessageResponse:
    """Убирает авторизационный cookie Authorization"""
    return await user_service.logout_user(
        user=user,
        response=response,
    )
