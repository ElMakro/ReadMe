from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from server.app.api.openapi_docs import openapi_extra_authorization_cookie_non_required
from server.app.api.v1.auth.auth_service import AuthService
from server.app.api.v1.common_schemas import MessageResponse
from server.app.api.v1.users.users import CreatedUserInfo, UserAuthentication, UserRegistration, UserVerification
from server.app.common_dependencies.depends import get_auth_user

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
        auth_service: AuthService = Depends(
            AuthService,
        ),
) -> CreatedUserInfo:
    """Создаёт пользователя в системе"""
    return await auth_service.register_user(
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
        },
    },
)
async def login(
        user: UserAuthentication,
        response: Response,
        auth_service: AuthService = Depends(
            AuthService,
        ),
) -> MessageResponse:
    """Идентифицирует и аутентифицирует пользователя. В случае корректности пользовательских данных кладёт
    авторизационный cookie Authorization с зашифрованным JWT токеном."""
    return await auth_service.login_user(
        user=user,
        response=response,
    )


@auth_router.get(
    path="/logout",
    status_code=status.HTTP_200_OK,
    summary="Выход пользователя из системы",
    response_model=MessageResponse,
    openapi_extra=openapi_extra_authorization_cookie_non_required,
)
async def logout(
        response: Response,
        user: Annotated[UserVerification, Depends(
            get_auth_user,
        )],
        auth_service: AuthService = Depends(
            AuthService,
        ),
) -> MessageResponse:
    """Убирает авторизационный cookie Authorization"""
    return await auth_service.logout_user(
        user=user,
        response=response,
    )
