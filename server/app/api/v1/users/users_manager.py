import uuid

from fastapi import Depends
from sqlalchemy import select

from server.app.api.v1.users.users import UserInfo, UserVerification
from server.config.db_dependency import DBDependency
from server.database.models import Users


class UserExistenceError(
    ValueError,
):
    """Исключение, связанное с существованием пользователя"""
    pass


class UsersManager:
    def __init__(
            self,
            db: DBDependency = Depends(
                DBDependency,
            ),
    ) -> None:
        self.db = db
        self.model = Users

    async def get_user_by_nickname(
            self,
            nickname: str,
    ) -> UserInfo | None:
        async with self.db.db_session() as session:
            query = select(
                self.model.id,
                self.model.nickname,
                self.model.email,
                self.model.role,
                self.model.password,
            ).where(
                self.model.nickname == nickname,
            )

            result = await session.execute(
                query,
            )
            user = result.mappings().first()
            return UserInfo(
                **user,
            ) if user else None

    async def get_user_by_id(
            self,
            user_id: uuid.UUID,
    ) -> UserVerification | None:
        async with self.db.db_session() as session:
            query = select(
                self.model.id,
                self.model.nickname,
                self.model.role,
            ).where(
                self.model.id == user_id,
            )

            result = await session.execute(
                query,
            )
            user = result.mappings().one_or_none()
            return UserVerification(
                **user,
            ) if user else None
