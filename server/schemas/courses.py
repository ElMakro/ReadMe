import uuid

from pydantic import BaseModel, ConfigDict, Field, RootModel

from server.schemas.common import TimestampsMixin


class CourseIDMixin(
    BaseModel,
):
    """Универсальная схема для необязательного поля уникального идентификатора курса"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: uuid.UUID = Field(
        description="Уникальный идентификатор курса",
        examples=[uuid.uuid4()],
    )


class CourseBase(
    BaseModel,
):
    """Базовая схема курса"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    name: str = Field(
        ...,
        description="Название курса",
        min_length=1,
        max_length=255,
        examples=["Название курса"],
    )
    description: str = Field(
        "",
        description="Описание курса",
        examples=["Описание курса"],
    )
    is_public: bool = Field(
        default=True,
        description="Видим ли курс для всех пользователей",
        examples=[True, False],
    )
    is_content_public: bool = Field(
        default=True,
        description="Видимо ли содержимое курса для всех пользователей",
        examples=[True, False],
    )


class CourseCreation(
    CourseBase,
):
    """Схема запроса на создание курса"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )


class CourseUpdate(
    BaseModel,
):
    """Схема запроса на изменение данных о курсе (все поля опциональны)"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    name: str | None = Field(
        None,
        description="Название курса",
        min_length=1,
        max_length=255,
        examples=["Название курса"],
    )
    description: str = Field(
        None,
        description="Описание курса",
        examples=["Описание курса"],
    )
    is_open: bool | None = Field(
        None,
        description="Открыт ли курс для записи",
        examples=[True, False],
    )
    is_public: bool = Field(
        default=None,
        description="Видим ли курс для всех пользователей",
        examples=[True, False],
    )
    is_content_public: bool = Field(
        default=None,
        description="Видимо ли содержимое курса для всех пользователей",
        examples=[True, False],
    )


class CourseChangeOwner(
    BaseModel,
):
    """Схема запроса на смену владельца курса"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    new_professor_id: uuid.UUID = Field(
        ...,
        description="Уникальный идентификатор нового преподавателя",
    )


class CourseResponse(
    CourseBase,
    CourseIDMixin,
    TimestampsMixin,
):
    """Схема ответа с полной информацией о курсе"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    professor_id: uuid.UUID = Field(
        ...,
        description="ID преподавателя",
    )


class CourseFullListResponse(
    BaseModel,
):
    """Схема ответа со списком полных информаций о курсах"""
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    courses: list[CourseResponse]
    total: int = Field(
        ...,
        ge=0,
        description="Количество курсов",
        examples=[1],
    )


class CourseByName(
    BaseModel,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    name: str = Field(
        description="Название курса",
        examples=["Название курса"],
        min_length=1,
        max_length=255,
    )


class CourseInfo(
    CourseIDMixin,
    CourseByName,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    description: str = Field(
        description="Описание курса",
    )


class CoursesList(
    RootModel[list[CourseInfo]],
):
    pass
