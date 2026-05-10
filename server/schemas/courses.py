import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CourseByID(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    course_id: uuid.UUID = Field(description="Уникальный идентификатор курса", examples=[uuid.uuid4()])


class CourseByName(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    course_name: str = Field(description="Название курса", examples=["Название курса"], min_length=1, max_length=255)


class CourseCreation(CourseByID, CourseByName):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    is_open: bool = Field(description="Открыт ли курс для записи (по умолчанию - открыт)", default=True,
                          examples=[True, False])


class CourseInformation(CourseCreation):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    path_to_directory: str = Field(description="Путь к директории, содержащей контент курса", examples=["/course"])


class CreatedCourseInformation(CourseByID):
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class CourseByNamePart(CourseByID, CourseByName):
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class PaginationParameters(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    page: int = Field(description="Номер страницы", examples=[1, 2, 3], default=1)
    records_per_page: Literal[5, 10, 15, 20, 30] = Field(description="Количество записей на странице", default=10)


class CoursesByNamePart(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    courses_ids: list[CourseByNamePart] = Field(description="Список курсов",
                                                examples=[[CourseByNamePart(course_id=uuid.uuid4(),
                                                                            course_name="Название курса")]])


class UserCourses(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    courses_list: list[CourseByID] = Field(description="Список ID курсов пользователя",
                                           examples=[[CourseByID(course_id=uuid.uuid4(), )]])
