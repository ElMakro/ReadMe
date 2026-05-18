import uuid

from fastapi import Depends, HTTPException
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from server.app.api.v1.users.users import CreatedUserInfo, NewUser, StoredUserInfo
from server.config.db_dependency import DBDependency
from server.config.redis_dependency import RedisDependency
from server.database.models import Users


class AuthManager:
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
            return CreatedUserInfo.model_validate(user_data)

    async def store_token(self, user_info: StoredUserInfo, user_id: uuid.UUID, session_id: str) -> None:
        async with self.redis.get_client() as client:
            await client.set(f"{user_id}:{session_id}", user_info.model_dump_json())

    async def get_user_info(self, user_id: uuid.UUID, session_id: str) -> StoredUserInfo | None:
        async with self.redis.get_client() as client:
            return StoredUserInfo.model_validate_json(await client.get(f"{user_id}:{session_id}"))

    async def clear_token(self, user_id: uuid.UUID, session_id: str) -> None:
        async with self.redis.get_client() as client:
            await client.delete(f"{user_id}:{session_id}")
