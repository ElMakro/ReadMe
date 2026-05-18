import uuid

from pydantic import BaseModel, ConfigDict, Field, RootModel


class NoteById(
    BaseModel,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    id: uuid.UUID = Field(
        description="Идентификатор конспекта",
        examples=[uuid.uuid4()],
    )

class NoteInfo(
    NoteById,
):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
    )

    name: str = Field(
        description="Название конспекта"
    )
    content: str = Field(
        description="Содержание конспекта"
    )
    topic_id: uuid.UUID = Field(
        description="Идентификатор темы",
        examples=[uuid.uuid4()],
    )
    topic_name: str = Field(
        description="Название темы"
    )


class NotesList(
    RootModel[list[NoteInfo]],
):
    pass
