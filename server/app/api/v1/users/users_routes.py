import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile, status
from starlette.responses import FileResponse

from server.app.api.openapi_docs import (
    openapi_extra_authorization_cookie_non_required,
    openapi_extra_authorization_cookie_required,
)
from server.app.api.v1.common_schemas import (
    APPLICATION_FIELDS_MISMATCH_ERROR_TEXT,
    APPLICATION_REFUSED_ERROR_TEXT,
    CANT_CHANGE_OWN_ROLE_ERROR_TEXT,
    CANT_DELETE_OWN_PROFILE_ERROR_TEXT,
    FORBIDDEN_ERROR_TEXT,
    NOT_EXISTING_LINK_ERROR_TEXT,
    NOT_FOUND_ERROR_TEXT,
    NOT_UNIQUE_FIELDS_ERROR_TEXT,
    UNAUTHORIZED_ERROR_TEXT,
    UNPROCESSABLE_ENTITY_ERROR_TEXT,
    UPDATED_LINK_ERROR_TEXT,
    USER_MUST_BE_IN_PROFESSORS_TABLE_ERROR_TEXT,
    WRONG_APPLICATION_LINK_ERROR_TEXT,
    PaginationParameters,
)
from server.app.api.v1.notes.exceptions import CantChangeOwnRoleError, CantDeleteOwnProfileError
from server.app.api.v1.users.exceptions import (
    ApplicationFieldsMismatchError,
    ApplicationRefusedError,
    NotExistingLinkError,
    NotUniqueFieldsError,
    UpdatedLinkError,
    UserMustBeInProfessorsTableError,
    UserNotFoundError,
)
from server.app.api.v1.users.users import (
    ApplicationById,
    ApplicationChangeStatus,
    ApplicationsList,
    ApplicationsUserList,
    ProfessorApplication,
    SecretApplicationLink,
    UserProfile,
    UsersList,
    UserUpdatedInfo,
    UserVerification,
    UserWithRole,
)
from server.app.api.v1.users.users_service import UsersService
from server.app.common_dependencies.depends import check_role, get_auth_user, get_current_user, get_new_link
from server.app.common_dependencies.secret_link_strategies import UpdatedLinkStrategy
from server.data.users_resources.users_resources_manager import UsersResourcesManager
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
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Пользователь не произвёл вход",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Некорректно переданы параметры",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": NOT_FOUND_ERROR_TEXT,
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
    return await users_service.get_info_for_user_profile(
        user,
    )


@users_router.put(
    "/profile",
    summary="Редактировать профиль пользователя",
    status_code=status.HTTP_200_OK,
    response_model=UserProfile,
    response_description="Профиль пользователя отредактирован",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
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
    return await users_service.update_user_profile(
        user_id=user.id,
        updated_info=updated_info,
    )


@users_router.get(
    path="/all",
    summary="Список пользователей",
    status_code=status.HTTP_200_OK,
    response_model=UsersList,
    response_description="Возвращена информация обо всех пользователях",
    responses={
        status.HTTP_403_FORBIDDEN: {
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


@users_router.get(
    path="/search",
    summary="Поиск пользователя",
    status_code=status.HTTP_200_OK,
    response_model=UsersList,
    response_description="Возвращена информация о соответствующих введённому шаблону пользователях",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": FORBIDDEN_ERROR_TEXT,
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Некорректно переданы параметры",
        },
    },
)
async def search_users(
        user: Annotated[UserVerification, Depends(
            check_role([Role.ADMIN]),
        )],
        search_pattern: str = Query(
            ...,
            description="Шаблон поиска"
        ),
        pagination_parameters: PaginationParameters = Depends(),
        users_service: UsersService = Depends(
            UsersService,
        ),
) -> UsersList:
    return await users_service.search_users(
        pattern=search_pattern,
        page=pagination_parameters.page,
        size=pagination_parameters.records_per_page,
    )


@users_router.put(
    path="/change-role",
    summary="Список пользователей",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Роль пользователя успешно изменена",
    responses={
        status.HTTP_403_FORBIDDEN: {
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
    return await users_service.change_role(user=changing_user, current_user_id=current_user.id)


@users_router.delete(
    path="/delete-user/{id}",
    summary="Удаление пользователя",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Пользователь удалён",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": FORBIDDEN_ERROR_TEXT,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": NOT_FOUND_ERROR_TEXT,
        },
        status.HTTP_409_CONFLICT: {
            "description": CANT_DELETE_OWN_PROFILE_ERROR_TEXT,
        }
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
    return await users_service.delete_user(id=id, current_user_id=user.id)


@users_router.get(
    path="/get-application-link",
    summary="Получить секретную ссылку для подачи заявки",
    status_code=status.HTTP_200_OK,
    response_model=SecretApplicationLink,
    response_description="Ссылка получена",
    responses={
        status.HTTP_403_FORBIDDEN         : {
            "description": FORBIDDEN_ERROR_TEXT,
        },
        status.HTTP_409_CONFLICT: {
            "description": NOT_EXISTING_LINK_ERROR_TEXT,
        },
    },
)
async def get_secret_application_link(
    user: Annotated[UserVerification, Depends(
            check_role([Role.ADMIN]),
    )],
    users_service: UsersService = Depends(
        UsersService,
    ),
) -> SecretApplicationLink:
    return await users_service.get_secret_application_link()


@users_router.post(
    path="/set-application-link",
    summary="Установить новую секретную ссылку для подачи заявки",
    status_code=status.HTTP_200_OK,
    response_model=SecretApplicationLink,
    response_description="Ссылка установлена",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": FORBIDDEN_ERROR_TEXT,
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UPDATED_LINK_ERROR_TEXT,
        }
    },
)
async def set_secret_application_link(
        user: Annotated[UserVerification, Depends(
            check_role([Role.ADMIN]),
        )],
        new_link_content: Annotated[UpdatedLinkStrategy, Depends(
            get_new_link
        )],
        users_service: UsersService = Depends(
            UsersService,
        ),
) -> SecretApplicationLink:
    return await users_service.set_secret_application_link(new_link_content)


@users_router.post(
    path="/submit-professor-application/{secret_link}",
    summary="Подать заявку на роль преподавателя",
    status_code=status.HTTP_201_CREATED,
    response_model=ApplicationById,
    response_description="Заявка успешно добавлена",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": FORBIDDEN_ERROR_TEXT,
        },
        status.HTTP_409_CONFLICT: {
            "description": APPLICATION_REFUSED_ERROR_TEXT
        },
        status.HTTP_404_NOT_FOUND: {
            "description": WRONG_APPLICATION_LINK_ERROR_TEXT,
        },
    },
)
async def submit_professor_application(
        user: Annotated[UserVerification, Depends(
            check_role([Role.STUDENT, Role.ADMIN]),
        )],
        application: ProfessorApplication,
        secret_link: str = Path(
            ...,
            description="Секретная ссылка для подачи заявки на роль преподавателя",
        ),
        users_service: UsersService = Depends(
            UsersService,
        ),
) -> ApplicationById:
    if not await users_service.verify_secret_link(secret_link):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_APPLICATION_LINK_ERROR_TEXT,
        )
    return await users_service.reg_professor_application(
        id=user.id,
        application=application,
    )


@users_router.get(
    path="/get-active-applications",
    summary="Получить список активных заявок на роль преподавателя",
    status_code=status.HTTP_200_OK,
    response_model=ApplicationsList,
    response_description="Список заявок получен",
    responses={
        status.HTTP_403_FORBIDDEN: {
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
        status.HTTP_403_FORBIDDEN: {
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
    return await users_service.change_application_status(application)


@users_router.get(
    path="/get-my-applications",
    summary="Получить список заявок пользователя на роль преподавателя",
    status_code=status.HTTP_200_OK,
    response_model=ApplicationsUserList,
    response_description="Список заявок пользователя получен",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
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
    summary="Записаться на курс",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Пользователь успешно записан на курс",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Пользователь не имеет прав на запись на данный курс",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Курса или пользователя с таким идентификатором не существует",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Пользователь уже записан на данный курс или является преподавателем данного курса",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie_non_required,
)
async def enroll(
        user: Annotated[UserVerification, Depends(
            get_auth_user,
        )],
        user_id: uuid.UUID = Query(
            None,
            description="Уникальный идентификатор пользователя. В случае, если он не передан, "
                        "то осуществляется запись текущего пользователя."
        ),
        course_id: uuid.UUID = Query(
            ...,
            description="Уникальный идентификатор курса",
        ),
        users_service: UsersService = Depends(
            UsersService,
        ),
) -> None:
    """Записать текущего пользователя на курс"""
    await users_service.enroll(
        user,
        user_id,
        course_id,
    )


@users_router.delete(
    "/unenroll",
    summary="Отписаться от курса",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Текущий пользователь успешно отписан от курса",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Курса или пользователя с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie_non_required,
)
async def unenroll(
        user: Annotated[UserVerification, Depends(
            get_auth_user,
        )],
        user_id: uuid.UUID = Query(
            None,
            description="Уникальный идентификатор пользователя. В случае, если он не передан, "
                        "то осуществляется запись текущего пользователя."
        ),
        course_id: uuid.UUID = Query(
            ...,
            description="Уникальный идентификатор курса",
        ),
        users_service: UsersService = Depends(
            UsersService,
        ),
):
    """Отписать текущего пользователя от курса"""
    await users_service.unenroll(
        user,
        user_id,
        course_id,
    )


@users_router.get(
    path="/enrolled-users/{course_id}",
    summary="Получить список пользователей, записанных на курс",
    status_code=status.HTTP_200_OK,
    response_description="Получен список записанных на курс пользователей",
    response_model=UsersList,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Пользователь не имеет прав на просмотр списка пользователей",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Курса с таким идентификатором не существует",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    },
    openapi_extra=openapi_extra_authorization_cookie_non_required,
)
async def get_enrolled_users(
        user: Annotated[UserVerification | None, Depends(
            get_current_user,
        )],
        course_id: uuid.UUID = Path(..., description="Уникальный идентификатор курса"),
        users_service: UsersService = Depends(UsersService),
) -> UsersList:
    return await users_service.get_enrolled_users(
        user,
        course_id,
    )


@users_router.post(
    "/icon",
    description="Установить иконку текущему пользователю",
    summary="Установить иконку пользователя",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "description": "Отправлен некорректный тип файла"
        }
    },
    openapi_extra=openapi_extra_authorization_cookie_required,
)
async def set_user_icon(
        user: Annotated[UserVerification, Depends(
            get_auth_user,
        )],
        icon_file: UploadFile = File(
            ...,
            description="Файл иконки пользователя",
        ),
        users_service: UsersService = Depends(UsersService)
) -> None:
    await users_service.set_user_icon(user, icon_file)


@users_router.get(
    path="/{user_id}/icon",
    summary="Получить иконку пользователя по его идентификатору",
    status_code=status.HTTP_200_OK,
    response_description="Файл иконки пользователя",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": NOT_FOUND_ERROR_TEXT
        }
    },
    openapi_extra=openapi_extra_authorization_cookie_required,
)
async def get_user_icon(user_id: uuid.UUID = Path(..., description="Уникальный идентификатор пользователя"),
                        users_resources_manager: UsersResourcesManager = Depends(
                            UsersResourcesManager)) -> FileResponse:
    return FileResponse(
        users_resources_manager.get_user_icon_path(user_id)
    )
