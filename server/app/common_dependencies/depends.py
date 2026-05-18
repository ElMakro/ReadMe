from typing import Annotated

from fastapi import Depends, HTTPException, status

from server.app.api.v1.auth.auth_handler import AuthHandler
from server.app.api.v1.auth.auth_manager import AuthManager
from server.app.api.v1.users.users import UserVerification
from server.app.common_dependencies.utils import get_token_from_cookies
from server.enums.role import Role


async def get_current_user(
        token: Annotated[str, Depends(get_token_from_cookies)],
        handler: AuthHandler = Depends(AuthHandler),
        manager: AuthManager = Depends(AuthManager),
) -> UserVerification:
    decoded_token = await handler.decode_token(token=token)
    user_id = decoded_token.get("user_id")
    session_id = decoded_token.get("session_id")
    if not (user_info := await manager.get_user_info(user_id=user_id, session_id=session_id)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен недействителен.")
    return UserVerification(id=user_id, role=user_info.role, email=user_info.email,
                            nickname=user_info.nickname, session_id=session_id)


async def check_role(
        allowed_roles: list[Role],
        user: UserVerification = Depends(get_current_user)
) -> UserVerification:
    if user.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return user
