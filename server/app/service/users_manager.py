import uuid

from fastapi import Depends, HTTPException
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from config.db_dependency import DBDependency
from config.redis_dependency import RedisDependency
from server.database.models import Users
from server.schemas.users import NewUser, CreatedUserInfo, UserInfo


class UsersManager:
    def __init__(self, db: DBDependency = Depends(DBDependency), redis: RedisDependency = Depends(RedisDependency)) \
            -> None:
        self.db = db
        self.redis = redis
        self.model = Users

    async def create_user(self, user: NewUser) -> CreatedUserInfo:
        async with self.db.db_session() as session:
            query = insert(self.model).values(**user.model_dump()).returning(self.model)

            try:
                result = await session.execute(query)
            except IntegrityError:
                raise HTTPException(status_code=400, detail="User already exists.")

            await session.commit()

            user_data = result.scalar_one()
            return CreatedUserInfo(**user_data.__dict__)

    async def get_user_by_nickname(self, nickname: str) -> UserInfo | None:
        async with self.db.db_session() as session:
            query = select(
                self.model.id,
                self.model.nickname,
                self.model.role,
                self.model.password
            ).where(self.model.nickname == nickname)

            result = await session.execute(query)
            user = result.mappings().first()
            return UserInfo(**user) if user else None

    async def store_token(self, token: str, user_id: uuid.UUID, session_id: str) -> None:
        async with self.redis.get_client() as client:
            await client.set(f"{user_id}:{session_id}", token)
