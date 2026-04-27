import datetime
import uuid
from typing import NamedTuple

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from server.config.settings import settings
from server.enums.role import Role


class CreatedTokenTuple(NamedTuple):
    encoded_jwt: str
    session_id: str


class AuthHandler:
    secret = settings.secret_key.get_secret_value()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def get_hashed_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    async def verify_password(self, entered_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(entered_password, hashed_password)

    async def create_token(self, user_id: uuid.UUID, user_role: Role) -> CreatedTokenTuple:
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=settings.access_token_expire)
        session_id = str(uuid.uuid4())
        payload = {
            "user_id": user_id,
            "role": user_role,
            "session_id": session_id,
            "exp": expire
        }
        encoded_jwt = jwt.encode(payload=payload, key=self.secret, algorithm="HS256")
        return CreatedTokenTuple(encoded_jwt=encoded_jwt, session_id=session_id)

    async def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(jwt=token, key=self.secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Срок действия временного ключа доступа истёк."
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен недействителен."
            )
