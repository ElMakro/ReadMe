import datetime
import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints

from server.enums.role import Role


class UserByID(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    id: uuid.UUID


class UserByEmail(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    email: EmailStr | None = None


class UserByNickname(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    nickname: Annotated[str, StringConstraints(min_length=4, max_length=32, to_lower=True,
                                               pattern=r'^[A-Za-z0-9_\-\.!@#$%^&*()+=?<>]+$')]


class UserRegistration(UserByNickname, UserByEmail):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    password: Annotated[str, StringConstraints(min_length=8, max_length=64)]


class UserAuthentication(UserByNickname):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    password: Annotated[str, StringConstraints(min_length=8, max_length=64)]


class NewUser(UserByNickname, UserByEmail):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    password: str
    role: Role = Role.STUDENT


class CreatedUserInfo(UserByID, UserByNickname):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    created_at: datetime.datetime
    updated_at: datetime.datetime


class UserInfo(UserByID, NewUser):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    pass


class UserVerification(UserByID, UserByNickname):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    role: Role
    session_id: uuid.UUID | str | None = None
