from fastapi import Depends, HTTPException
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from config.db_dependency import DBDependency
from server.database.models import Users
from server.schemas.users import NewUser, CreatedUserInfo


class UsersManager:
    def __init__(self, db: DBDependency = Depends(DBDependency)) -> None:
        self.db = db
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
