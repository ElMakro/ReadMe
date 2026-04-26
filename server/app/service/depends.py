import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status

from server.app.service.auth_handler import AuthHandler
from server.app.service.users_manager import UsersManager
from server.app.service.utils import get_token_from_cookies
from server.enums.role import Role
from server.schemas.users import UserVerification


async def get_current_user(
    token: Annotated[str, Depends(get_token_from_cookies)],
    handler: AuthHandler = Depends(AuthHandler),
    manager: UsersManager = Depends(UsersManager),
) -> UserVerification:
    decoded_token = await handler.decode_token(token=token)
    user_id = decoded_token.get("user_id")
    session_id = decoded_token.get("session_id")
    if not await manager.get_token(user_id=user_id, session_id=session_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен недействителен.")
    user = await manager.get_user_by_id(user_id=uuid.UUID(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден.")
    return UserVerification(id=user_id, role=user.role, nickname=user.nickname, session_id=session_id)

async def check_role(
    allowed_roles: list[Role],
    user: UserVerification = Depends(get_current_user)
):
    if user.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return user
