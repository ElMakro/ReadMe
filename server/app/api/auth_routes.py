from fastapi import APIRouter, status
from fastapi.params import Depends
from fastapi.responses import JSONResponse

from server.app.service.users_service import UsersService
from server.schemas.users import UserRegistration, CreatedUserInfo, UserAuthentication

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post(
    path="/reg",
    response_model=CreatedUserInfo,
    status_code=status.HTTP_201_CREATED
)
async def register_user(user: UserRegistration, user_service: UsersService = Depends(UsersService)) -> CreatedUserInfo:
    return await user_service.register_user(user=user)


@auth_router.post(
    path="/login",
    status_code=status.HTTP_200_OK
)
async def login(user: UserAuthentication, user_service: UsersService = Depends(UsersService)) -> JSONResponse:
    return await user_service.login_user(user=user)