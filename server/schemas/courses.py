import uuid
from typing import List

from pydantic import BaseModel, ConfigDict, Field, RootModel


class CourseByID(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    course_id: uuid.UUID = Field(description="Уникальный идентификатор курса", examples=[uuid.uuid4()])


class CourseByName(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    course_name: str = Field(description="Название курса", examples=["Название курса"], min_length=1, max_length=255)


class CourseInfo(CourseByID, CourseByName):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    description: str = Field(description="Описание курса")


class CoursesList(RootModel[List[CourseInfo]]):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
