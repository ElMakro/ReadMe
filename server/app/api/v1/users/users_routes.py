from typing import Annotated

from fastapi import APIRouter, Depends, status

from server.app.api.v1.users.users import UserProfile, UserVerification
from server.app.api.v1.users.users_service import UsersService
from server.app.common_dependencies.depends import get_auth_user

users_router = APIRouter(
    prefix="/users",
    tags=["Взаимодействие с пользователями"],
)


@users_router.get(
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
async def user_profile(
        user: Annotated[UserVerification | None, Depends(
            get_auth_user,
        )],
        users_service: UsersService = Depends(
            UsersService,
        ),
):
    return users_service.get_info_for_user_profile(
        user,
    )


@users_router.post(
    "/enroll",
    summary="Записать другого студента на курс",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
)
async def enroll_other_student():
    # TODO: Когда-нибудь дописать маршрут и схемы
    pass


@users_router.post(
    "/unenroll",
    summary="Отписать другого студента от курса",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
)
async def unenroll_other_student():
    # TODO: Когда-нибудь дописать маршрут и схемы
    pass
