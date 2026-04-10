import uuid
import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, EmailStr, StringConstraints

from server.enums.role import Role


class UserByID(BaseModel):
    id: uuid.UUID


class UserByEmail(BaseModel):
    email: Optional[EmailStr] = None


class UserByNickname(BaseModel):
    nickname: Annotated[str, StringConstraints(min_length=4, max_length=32, to_lower=True,
                                               pattern=r'^[A-Za-z0-9_\-\.!@#$%^&*()+=?<>]+$')]


class UserRegistration(UserByNickname, UserByEmail):
    password: Annotated[str, StringConstraints(min_length=8, max_length=64)]


class NewUser(UserByNickname, UserByEmail):
    password: str
    role: Role = Role.STUDENT


class CreatedUserInfo(UserByID, UserByNickname):
    created_at: datetime.datetime
    updated_at: datetime.datetime
