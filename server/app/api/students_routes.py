from typing import Annotated

from fastapi import APIRouter, status, Depends

from server.app.service.depends import get_current_user
from server.app.service.students_service import StudentsService
from server.schemas.users import UserVerification, UserProfile

students_router = APIRouter(
    prefix="/students",
    tags=["Взаимодействие со студентами"],
)


@students_router.get(
    "/profile",
    summary="Профиль пользователя",
    status_code=status.HTTP_200_OK,
    response_model=UserProfile,
    response_description="Возвращена информация о пользователе",
    responses={
        status.HTTP_401_UNAUTHORIZED         : {
            "description": "Пользователь не произвёл вход",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Некорректно переданы параметры",
        },
    },
)
async def student_profile(
    user: Annotated[UserVerification, Depends(
                get_current_user,
            )],
    student_service: StudentsService = Depends(StudentsService),
):
    return student_service.get_info_for_user_profile(user)


@students_router.post(
    "/enroll",
    summary="Записать другого студента на курс",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
)
async def enroll_other_student():
    # TODO: Когда-нибудь дописать маршрут и схемы
    pass


@students_router.post(
    "/unenroll",
    summary="Отписать другого студента от курса",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
)
async def unenroll_other_student():
    # TODO: Когда-нибудь дописать маршрут и схемы
    pass
