import datetime
import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, RootModel, StringConstraints

from server.enums.application_status import ApplicationStatus
from server.enums.role import Role


class UserByID(
    BaseModel,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    id: uuid.UUID = Field(
        description="Идентификатор пользователя",
        examples=[uuid.uuid4()],
    )


class UserByEmail(
    BaseModel,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    email: EmailStr | None = Field(
        None,
        description="Адрес электронной почты пользователя",
        examples=[
            "readme.ivt.yarsu@mail.ru"],
    )


class UserByNickname(
    BaseModel,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    nickname: Annotated[str, StringConstraints(
        min_length=4,
        max_length=32,
        to_lower=True,
        pattern=r'^[A-Za-z0-9_\-\.!@#$%^&*()+=?<>]+$',
    )] = Field(
        description="Никнейм пользователя",
        examples=["nickname"],
    )


class UserRegistration(
    UserByNickname,
    UserByEmail,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    password: Annotated[str, StringConstraints(
        min_length=8,
        max_length=64,
    )] = Field(
        description="Пароль",
        examples=["password"],
    )


class UserAuthentication(
    UserByNickname,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    password: Annotated[str, StringConstraints(
        min_length=8,
        max_length=64,
    )] = Field(
        description="Пароль",
        examples=["password"],
    )


class NewUser(
    UserByNickname,
    UserByEmail,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    password: str = Field(
        description="Пароль",
        examples=["password"],
    )
    role: Role = Role.STUDENT


class CreatedUserInfo(
    UserByID,
    UserByNickname,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    created_at: datetime.datetime = Field(
        description="Временная отметка создания пользователя",
        examples=[uuid.uuid4()],
    )
    updated_at: datetime.datetime = Field(
        description="Временная отметка изменения пользователя",
        examples=[uuid.uuid4()],
    )


class UserInfo(
    UserByID,
    NewUser,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    pass


class UserVerification(
    UserByID,
    UserByNickname,
    UserByEmail,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    role: Role
    session_id: uuid.UUID | str | None = None


class UserProfile(
    UserByID,
    UserByNickname,
    UserByEmail
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    role: Role


class UserUpdatedInfo(
    UserByNickname,
    UserByEmail,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )


class UsersList(
    RootModel[list[UserProfile]]
):
    pass


class UserWithRole(
    UserByID
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    role: Role


class ApplicationById(
    BaseModel,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    id: uuid.UUID = Field(
        description="Идентификатор заявки",
        examples=[uuid.uuid4()],
    )


class ProfessorApplication(
    BaseModel,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    name: str = Field(
        description="Имя преподавателя",
    )
    surname: str = Field(
        description="Фамилия преподавателя"
    )
    patronymic: str | None = Field(
        description="Отчество преподавателя",
        default=None,
    )


class ApplicationInfo(
    BaseModel,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    application_id: uuid.UUID = Field(
        description="Идентификатор заявки",
        examples=[uuid.uuid4()],
    )
    user_id: uuid.UUID = Field(
        description="Идентификатор пользователя, подавшего заявку",
        examples=[uuid.uuid4()],
    )
    name: str = Field(
        description="Имя преподавателя",
    )
    surname: str = Field(
        description="Фамилия преподавателя"
    )
    patronymic: str | None = Field(
        description="Отчество преподавателя",
        default=None,
    )
    status: ApplicationStatus = Field(
        description="Статус заявки",
        examples=[ApplicationStatus.PENDING],
    )
    created_at: datetime.datetime = Field(
        description="Время создания заявки",
        examples=[datetime.datetime.now()],
    )
    updated_at: datetime.datetime = Field(
        description="Время изменения состояния заявки",
        examples=[datetime.datetime.now()],
    )


class ApplicationsList(
    RootModel[list[ApplicationInfo]]
):
    pass


class ApplicationChangeStatus(
    BaseModel,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    application_id: uuid.UUID = Field(
        description="Идентификатор заявки",
        examples=[uuid.uuid4()],
    )
    user_id: uuid.UUID = Field(
        description="Идентификатор пользователя, подавшего заявку",
        examples=[uuid.uuid4()],
    )
    status: ApplicationStatus = Field(
        description="Статус заявки",
        examples=[ApplicationStatus.PENDING],
    )

    admin_comment: str | None = Field(
        description="Комментарий к изменению статуса заявки (рекомендуется при отказе)",
        default=None
    )


class ApplicationUserInfo(
    ApplicationInfo,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    admin_comment: str | None = Field(
        description="Комментарий к изменению статуса заявки (рекомендуется при отказе)",
        default=None
    )


class ApplicationsUserList(
    RootModel[list[ApplicationUserInfo]]
):
    pass
