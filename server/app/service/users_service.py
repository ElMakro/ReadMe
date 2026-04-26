from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from config.settings import settings
from server.app.service.auth_handler import AuthHandler
from server.app.service.users_manager import UsersManager
from server.schemas.users import UserRegistration, CreatedUserInfo, NewUser, UserAuthentication


class UsersService:
    def __init__(self, manager: UsersManager, auth_handler: AuthHandler) -> None:
        self.manager = manager
        self.auth_handler = auth_handler

    async def register_user(self, user: UserRegistration) -> CreatedUserInfo:
        hashed_password = self.auth_handler.get_hashed_password(user.password)
        new_user = NewUser(email=user.email, nickname=user.nickname, password=hashed_password)
        return await self.manager.create_user(user=new_user)

    async def login_user(self, user: UserAuthentication) -> JSONResponse:
        existing_user = self.manager.get_user_by_nickname(user.nickname)
        if existing_user is None or not await self.auth_handler.verify_password(
                entered_password=user.password, hashed_password=existing_user.password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверное имя пользователя или пароль."
            )
        token, session_id = await self.auth_handler.create_token(existing_user.id, existing_user.role)
        await self.manager.store_token(token=token, user_id=existing_user.id, session_id=session_id)

        response = JSONResponse(content={"message": "Успешный вход"})
        response.set_cookie(
            key="Authorization",
            value=token,
            httponly=True,
            max_age=settings.token_expire
        )
        return response