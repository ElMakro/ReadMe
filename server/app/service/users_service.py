from server.app.service.auth_handler import AuthHandler
from server.app.service.users_manager import UsersManager
from server.schemas.users import UserRegistration, CreatedUserInfo, NewUser


class UsersService:
    def __init__(self, manager: UsersManager, auth_handler: AuthHandler) -> None:
        self.manager = manager
        self.auth_handler = auth_handler

    async def register_user(self, user: UserRegistration) -> CreatedUserInfo:
        hashed_password = self.auth_handler.get_hashed_password(user.password)
        new_user = NewUser(email=user.email, nickname=user.nickname, password=hashed_password)
        return await self.manager.create_user(user=new_user)