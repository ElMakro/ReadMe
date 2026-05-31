import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from server.app.api.v1.common_schemas import (
    APPLICATION_FIELDS_MISMATCH_ERROR_TEXT,
    APPLICATION_REFUSED_ERROR_TEXT,
    CANT_CHANGE_OWN_ROLE_ERROR_TEXT,
    FORBIDDEN_ERROR_TEXT,
    NOT_FOUND_ERROR_TEXT,
    NOT_UNIQUE_FIELDS_ERROR_TEXT,
    UNAUTHORIZED_ERROR_TEXT,
    USER_MUST_BE_IN_PROFESSORS_TABLE_ERROR_TEXT,
    PaginationParameters,
)
from server.app.api.v1.notes.exceptions import CantChangeOwnRoleError
from server.app.api.v1.users.exceptions import (
    ApplicationFieldsMismatchError,
    ApplicationRefusedError,
    NotUniqueFieldsError,
    UserMustBeInProfessorsTableError,
    UserNotFoundError,
)
from server.app.api.v1.users.users import (
    ApplicationById,
    ApplicationChangeStatus,
    ApplicationsList,
    ApplicationsUserList,
    ProfessorApplication,
    UserProfile,
    UsersList,
    UserUpdatedInfo,
    UserVerification,
    UserWithRole,
)
from server.app.api.v1.users.users_service import UsersService
from server.app.common_dependencies.depends import check_role, get_auth_user
from server.enums.role import Role

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
) -> UserProfile:
    return users_service.get_info_for_user_profile(
        user,
    )


@users_router.put(
"/profile",
    summary="Редактировать профиль пользователя",
    status_code=status.HTTP_200_OK,
    response_model=UserProfile,
    response_description="Профиль пользователя отредактирован",
    responses={
        status.HTTP_401_UNAUTHORIZED         : {
            "description": "Пользователь не произвёл вход",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Некорректно переданы параметры",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": NOT_FOUND_ERROR_TEXT,
        },
        status.HTTP_409_CONFLICT: {
            "description": NOT_UNIQUE_FIELDS_ERROR_TEXT,
        },
    },
)
async def update_profile(
    user: Annotated[UserVerification | None, Depends(
        get_auth_user,
    )],
    updated_info: UserUpdatedInfo,
    users_service: UsersService = Depends(
        UsersService,
    ),
) -> UserProfile:
    try:
        return await users_service.update_user_profile(
            user_id=user.id,
            updated_info=updated_info,
        )
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
    except NotUniqueFieldsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@users_router.get(
    path="/all",
    summary="Список пользователей",
    status_code=status.HTTP_200_OK,
    response_model=UsersList,
    response_description="Возвращена информация обо всех пользователях",
    responses={
        status.HTTP_403_FORBIDDEN         : {
            "description": FORBIDDEN_ERROR_TEXT,
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Некорректно переданы параметры",
        },
    },
)
async def get_all_users(
    user: Annotated[UserVerification, Depends(
            check_role([Role.ADMIN]),
    )],
    pagination_parameters: PaginationParameters = Depends(),
    users_service: UsersService = Depends(
        UsersService,
    ),
) -> UsersList:
    return await users_service.get_all_users(
        page=pagination_parameters.page,
        size=pagination_parameters.records_per_page,
    )

@users_router.put(
    path="/change-role",
    summary="Список пользователей",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Роль пользователя успешно изменена",
    responses={
        status.HTTP_403_FORBIDDEN         : {
            "description": FORBIDDEN_ERROR_TEXT,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": NOT_FOUND_ERROR_TEXT,
        },
        status.HTTP_409_CONFLICT: {
            "description": USER_MUST_BE_IN_PROFESSORS_TABLE_ERROR_TEXT,
        },
        status.HTTP_409_CONFLICT: {
            "description": CANT_CHANGE_OWN_ROLE_ERROR_TEXT,
        }
    },
)
async def change_user_role(
    current_user: Annotated[UserVerification, Depends(
            check_role([Role.ADMIN]),
    )],
    changing_user: UserWithRole,
    users_service: UsersService = Depends(
        UsersService,
    ),
):
    try:
        return await users_service.change_role(user=changing_user, current_user_id=current_user.id)
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            )
        )
    except (UserMustBeInProfessorsTableError, CantChangeOwnRoleError) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(
                error,
            )
        )

@users_router.delete(
    path="/delete-user/{id}",
    summary="Удаление пользователя",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Пользователь удалён",
    responses={
        status.HTTP_403_FORBIDDEN         : {
            "description": FORBIDDEN_ERROR_TEXT,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": NOT_FOUND_ERROR_TEXT,
        },
    },
)
async def delete_user(
    user: Annotated[UserVerification, Depends(
            check_role([Role.ADMIN]),
    )],
    id: uuid.UUID = Path(
        ...,
        description="Уникальный идентификатор пользователя",
    ),
    users_service: UsersService = Depends(
        UsersService,
    ),
):
    try:
        return await users_service.delete_user(id=id)
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            )
        )

@users_router.post(
    path="/submit-professor-application",
    summary="Подать заявку на роль преподавателя",
    status_code=status.HTTP_201_CREATED,
    response_model=ApplicationById,
    response_description="Заявка успешно добавлена",
    responses={
        status.HTTP_403_FORBIDDEN         : {
            "description": FORBIDDEN_ERROR_TEXT,
        },
        status.HTTP_409_CONFLICT: {
            "description": APPLICATION_REFUSED_ERROR_TEXT
        }
    },
)
async def submit_professor_application(
    user: Annotated[UserVerification, Depends(
            check_role([Role.STUDENT, Role.ADMIN]),
    )],
    application: ProfessorApplication,
    users_service: UsersService = Depends(
        UsersService,
    ),
) -> ApplicationById:
    try:
        return await users_service.reg_professor_application(
            id=user.id,
            application=application,
        )
    except ApplicationRefusedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )

@users_router.get(
    path="/get-active-applications",
    summary="Получить список активных заявок на роль преподавателя",
    status_code=status.HTTP_200_OK,
    response_model=ApplicationsList,
    response_description="Список заявок получен",
    responses={
        status.HTTP_403_FORBIDDEN         : {
            "description": FORBIDDEN_ERROR_TEXT,
        },
    },
)
async def get_professor_applications(
    user: Annotated[UserVerification, Depends(
            check_role([Role.ADMIN]),
    )],
    pagination_parameters: PaginationParameters = Depends(),
    users_service: UsersService = Depends(
        UsersService,
    ),
) -> ApplicationsList:
    return await users_service.get_professor_applications(
        page=pagination_parameters.page,
        size=pagination_parameters.records_per_page,
    )

@users_router.put(
    path="/change-application-status",
    summary="Изменить статус заявки на роль преподавателя",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Статус заявки изменён",
    responses={
        status.HTTP_403_FORBIDDEN         : {
            "description": FORBIDDEN_ERROR_TEXT,
        },
        status.HTTP_409_CONFLICT: {
            "description": APPLICATION_FIELDS_MISMATCH_ERROR_TEXT,
        },
    },
)
async def change_application_status(
    user: Annotated[UserVerification, Depends(
            check_role([Role.ADMIN]),
    )],
    application: ApplicationChangeStatus,
    users_service: UsersService = Depends(
        UsersService,
    ),
):
    try:
        return await users_service.change_application_status(application)
    except ApplicationFieldsMismatchError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

@users_router.get(
    path="/get-my-applications",
    summary="Получить список заявок пользователя на роль преподавателя",
    status_code=status.HTTP_200_OK,
    response_model=ApplicationsUserList,
    response_description="Список заявок пользователя получен",
    responses={
        status.HTTP_401_UNAUTHORIZED         : {
            "description": UNAUTHORIZED_ERROR_TEXT,
        },
    },
)
async def get_my_applications(
    user: Annotated[UserVerification, Depends(
            get_auth_user,
    )],
    pagination_parameters: PaginationParameters = Depends(),
    users_service: UsersService = Depends(
        UsersService,
    ),
) -> ApplicationsUserList:
    return await users_service.get_user_applications(
        id=user.id,
        page=pagination_parameters.page,
        size=pagination_parameters.records_per_page
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
