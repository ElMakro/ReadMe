import uuid

from fastapi import Depends
from sqlalchemy import select, update

from server.app.api.v1.common_schemas import NOT_FOUND_ERROR_TEXT
from server.app.api.v1.users.exceptions import UserNotFoundError
from server.app.api.v1.users.users import UserInfo, UsersList, UserVerification
from server.config.db_dependency import DBDependency
from server.database.models import Users
from server.enums.role import Role


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

    async def get_all_users(self, offset: int, limit: int) -> UsersList:
        async with (self.db.db_session() as session):
            query = select(
                self.model.id,
                self.model.nickname,
                self.model.email,
                self.model.role,
            ).order_by(
                self.model.nickname,
            ).offset(
                offset,
            ).limit(
                limit,
            )
            result = await session.execute(
                query,
            )
            users = result.mappings().all()
            return UsersList.model_validate(
                users,
            )

    async def change_role(self, id: uuid.UUID, role: Role) -> None:
        async with (self.db.db_session() as session):
            query = update(
                self.model
            ).where(
                self.model.id == id
            ).values(
                role=role
            )
            result = await session.execute(query)
            await session.commit()
            if not result.rowcount:
                raise UserNotFoundError(NOT_FOUND_ERROR_TEXT)
            return
