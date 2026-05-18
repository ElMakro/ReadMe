from fastapi import Depends, HTTPException, Response, status

from server.app.api.v1.auth.auth_handler import AuthHandler
from server.app.api.v1.auth.auth_manager import AuthManager
from server.app.api.v1.common_schemas import MessageResponse
from server.app.api.v1.users.users import (
    CreatedUserInfo,
    NewUser,
    StoredUserInfo,
    UserAuthentication,
    UserRegistration,
    UserVerification,
)
from server.app.api.v1.users.users_manager import UsersManager
from server.config.settings import settings


class AuthService:
    def __init__(
            self,
            auth_manager: AuthManager = Depends(
                AuthManager,
            ),
            auth_handler: AuthHandler = Depends(
                AuthHandler,
            ),
            users_manager: UsersManager = Depends(
                UsersManager,
            ),
    ) -> None:
        self.auth_manager = auth_manager
        self.auth_handler = auth_handler
        self.users_manager = users_manager

    async def register_user(
            self,
            user: UserRegistration,
    ) -> CreatedUserInfo:
        hashed_password = await self.auth_handler.get_hashed_password(
            user.password,
        )
        new_user = NewUser(
            email=user.email,
            nickname=user.nickname,
            password=hashed_password,
        )
        return await self.auth_manager.create_user(
            user=new_user,
        )

    async def login_user(
            self,
            user: UserAuthentication,
            response: Response,
    ) -> MessageResponse:
        existing_user = await self.users_manager.get_user_by_nickname(
            user.nickname,
        )
        if existing_user is None or not await self.auth_handler.verify_password(
                entered_password=user.password,
                hashed_password=existing_user.password,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверное имя пользователя или пароль.",
            )
        token, session_id = await self.auth_handler.create_token(
            existing_user.id,
        )
        await self.auth_manager.store_token(
            user_info=StoredUserInfo(
                token=token,
                nickname=existing_user.nickname,
                email=existing_user.email,
                role=existing_user.role, ),
            user_id=existing_user.id,
            session_id=session_id,
        )

        response.set_cookie(
            key="Authorization",
            value=token,
            httponly=True,
            max_age=settings.token_expire,
        )

        return MessageResponse(
            message="Успешный вход",
            details=None,
        )

    async def logout_user(
            self,
            user: UserVerification,
            response: Response,
    ) -> MessageResponse:
        await self.auth_manager.clear_token(
            user_id=user.id,
            session_id=user.session_id,
        )
        response.delete_cookie(
            "Authorization",
        )
        return MessageResponse(
            message="Успешный выход",
            details=None,
        )
