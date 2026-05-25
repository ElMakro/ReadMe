from typing import Annotated

from fastapi import Depends, HTTPException, status

from server.app.api.v1.auth.auth_handler import AuthHandler
from server.app.api.v1.auth.auth_manager import AuthManager
from server.app.api.v1.common_schemas import FORBIDDEN_ERROR_TEXT
from server.app.api.v1.users.users import UserVerification
from server.app.api.v1.users.users_manager import UsersManager
from server.app.common_dependencies.utils import get_token_from_cookies
from server.enums.role import Role


async def get_current_user(
        token: Annotated[str | None, Depends(get_token_from_cookies)],
        handler: AuthHandler = Depends(AuthHandler),
        auth_manager: AuthManager = Depends(AuthManager),
        user_manager: UsersManager = Depends(UsersManager),
) -> UserVerification | None:
    if token is None:
        return None
    decoded_token = await handler.decode_token(token=token)
    user_id = decoded_token.get("user_id")
    session_id = decoded_token.get("session_id")
    if not await auth_manager.get_token(user_id=user_id, session_id=session_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен недействителен.")
    user = await user_manager.get_user_by_id(user_id)
    return UserVerification(id=user_id, role=user.role, email=user.email,
                            nickname=user.nickname, session_id=session_id)


async def get_auth_user(
        user: UserVerification | None = Depends(get_current_user),
) -> UserVerification:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не произвёл вход.")
    return user


def check_role(
        allowed_roles: list[Role],
):
    async def verification(
            user: UserVerification = Depends(get_auth_user)
    ) -> UserVerification:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=FORBIDDEN_ERROR_TEXT
            )
        return user
    return verification
