import uuid
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from server.app.service.courses_service import CoursesService
from server.app.service.depends import get_current_user
from server.schemas.courses import (
    CourseCreation,
    CourseInformation,
    CoursesByNamePart,
    CreatedCourseInformation,
    PaginationParameters,
    UserCourses,
)
from server.schemas.users import UserVerification

courses_router = APIRouter(prefix="/courses", tags=["Взаимодействие с курсами"])


@courses_router.post(
    "/create_course",
    summary="Создать новый курс",
    status_code=status.HTTP_201_CREATED,
    response_model=CreatedCourseInformation,
    response_description="Новый курс успешно создан",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Пользователь не имеет прав на создание курса"
        },
    },
)
async def create_course(
        course: CourseCreation,
        courses_service: CoursesService = Depends(CoursesService),
):
    """
    Создать новый курс, в котором текущий пользователь будет преподавателем
    """
    return await courses_service.create_course(course=course)


@courses_router.get(
    "/{course_id}",
    summary="Получить курс по его ID",
    status_code=status.HTTP_200_OK,
    response_model=CourseInformation,
    response_description="Курс успешно найден",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Пользователь не имеет прав на просмотр данного курса"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Курса с таким ID не существует"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Некорректно передан параметр пути"
        }
    }
)
async def get_course_by_id(
        course_id: UUID = Path(..., description="ID курса", examples=[uuid.uuid4()]),
        courses_service: CoursesService = Depends(CoursesService),
) -> CourseInformation:
    """Получить курс по его ID. Получение возможно только в том случае, если пользователь имеет
    достаточно прав для просмотра данного курса."""
    pass


@courses_router.get(
    "/{course_name}",
    summary="Получить ID курсов по началу их названий",
    status_code=status.HTTP_200_OK,
    response_model=CoursesByNamePart,
    response_description="Курсы найдены",
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Некорректно переданы параметры"
        }
    },
)
async def get_course_by_name_part(
        course_name: str = Path(..., description="Название курса"),
        pagination_parameters: PaginationParameters = Depends(PaginationParameters),
        courses_service: CoursesService = Depends(CoursesService),
) -> CoursesByNamePart:
    """Получить список ID курсов по началу их названий"""
    pass


@courses_router.put(
    "/my_courses",
    summary="Получить курсы текущего пользователя",
    status_code=status.HTTP_200_OK,
    response_model=UserCourses,
    response_description="Курсы найдены",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Пользователь не произвёл вход"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Некорректно переданы параметры"
        }
    }
)
async def get_my_courses(user: Annotated[UserVerification, Depends(get_current_user)],
                         pagination_parameters: PaginationParameters = Depends(PaginationParameters)) -> UserCourses:
    pass
