from fastapi import Depends, HTTPException, Response, status

from server.app.service.auth_handler import AuthHandler
from server.app.service.users_manager import UsersManager
from server.config.settings import settings
from server.schemas.common import MessageResponse
from server.schemas.users import CreatedUserInfo, NewUser, UserAuthentication, UserRegistration, UserVerification, \
    StoredUserInfo


class UsersService:
    def __init__(
            self,
            manager: UsersManager = Depends(
                UsersManager,
            ),
            auth_handler: AuthHandler = Depends(
                AuthHandler,
            ),
    ) \
            -> None:
        self.manager = manager
        self.auth_handler = auth_handler

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
        return await self.manager.create_user(
            user=new_user,
        )

    async def login_user(
            self,
            user: UserAuthentication,
            response: Response,
    ) -> MessageResponse:
        existing_user = await self.manager.get_user_by_nickname(
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
        await self.manager.store_token(
            user_info=StoredUserInfo(token=token,
                                     nickname=existing_user.nickname,
                                     email=existing_user.email,
                                     role=existing_user.role,),
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
            message="Успешный выход",
            details=None,
        )

    async def logout_user(
            self,
            user: UserVerification,
            response: Response,
    ) -> MessageResponse:
        await self.manager.clear_token(
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
