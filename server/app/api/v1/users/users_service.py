import re
import uuid
from uuid import UUID

from fastapi import Depends, UploadFile

from server.app.api.v1.auth.auth_manager import AuthManager
from server.app.api.v1.common_schemas import (
    CANT_CHANGE_OWN_ROLE_ERROR_TEXT,
    CANT_DELETE_OWN_PROFILE_ERROR_TEXT,
    NOT_EXISTING_LINK_ERROR_TEXT,
    UPDATED_LINK_ERROR_TEXT,
)
from server.app.api.v1.courses.courses import CourseResponse
from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.exceptions import ConflictError, MediaTypeError, ObjectMissingError, OperationPermissionError
from server.app.api.v1.notes.exceptions import CantChangeOwnRoleError, CantDeleteOwnProfileError
from server.app.api.v1.users.exceptions import NotExistingLinkError, UpdatedLinkError
from server.app.api.v1.users.secret_application_link_handler import SecretApplicationLinkHandler
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
from server.app.api.v1.users.users_manager import UsersManager
from server.app.common_dependencies.secret_link_strategies import UpdatedLinkStrategy
from server.config.constants import ALLOWED_LINK_CHARACTERS
from server.config.settings import settings
from server.data.users_resources.users_resources_manager import UsersResourcesManager
from server.enums.access_permissions import AccessPermissions
from server.enums.role import Role


class UsersService:
    def __init__(
            self,
            auth_manager: AuthManager = Depends(
                AuthManager,
            ),
            users_manager: UsersManager = Depends(
                UsersManager,
            ),
            courses_manager: CoursesManager = Depends(
                CoursesManager,
            ),
            users_resources_manager: UsersResourcesManager = Depends(
                UsersResourcesManager),
            secret_link_handler: SecretApplicationLinkHandler = Depends(
                SecretApplicationLinkHandler,
            ),
    ) -> None:
        self.auth_manager = auth_manager
        self.users_manager = users_manager
        self.courses_manager = courses_manager
        self.secret_link_handler = secret_link_handler
        self.users_resources_manager = users_resources_manager

    async def get_info_for_user_profile(
            self,
            user: UserVerification,
    ) -> UserProfile:
        return await self.users_manager.get_user_profile_info(user_id=user.id)

    async def update_user_profile(
            self,
            user_id: UUID,
            updated_info: UserUpdatedInfo,
    ) -> UserProfile:
        return await self.users_manager.update_user_profile(user_id=user_id, updated_info=updated_info)

    async def check_course_access(
            self,
            user: UserVerification | None,
            course_id: UUID | None = None,
            course: CourseResponse | None = None,
    ) -> AccessPermissions:
        if user is not None:
            if user.role == Role.ADMIN:
                return AccessPermissions.EDIT_ACCESS

        if course is None:
            if course_id is None:
                raise ValueError(
                    "Либо курс, либо его идентификатор должны быть переданы!",
                )
            else:
                course = await self.courses_manager.get_course_by_id(
                    course_id,
                )

        if course_id is None:
            course_id = course.id

        if user is not None:
            if course.professor_id == user.id:
                return AccessPermissions.EDIT_ACCESS

        if course.is_content_public:
            return AccessPermissions.CONTENT_ACCESS

        if course.is_public:
            return AccessPermissions.HEADER_ACCESS

        if user is not None:
            if await self.courses_manager.check_is_user_enrolled_on_course(
                    user.id,
                    course_id,
            ):
                return AccessPermissions.CONTENT_ACCESS

        return AccessPermissions.NO_ACCESS

    async def get_all_users(self, page: int, size: int) -> UsersList:
        offset = (page - 1) * size
        limit = size
        return await self.users_manager.get_all_users(
            offset,
            limit,
        )

    async def search_users(self, pattern: str, page: int, size: int) -> UsersList:
        offset = (page - 1) * size
        limit = size
        return await self.users_manager.search_users(
            pattern,
            offset,
            limit,
        )

    async def change_role(self, user: UserWithRole, current_user_id: uuid.UUID) -> None:
        if current_user_id == user.id:
            raise CantChangeOwnRoleError(CANT_CHANGE_OWN_ROLE_ERROR_TEXT)
        if user.role == Role.PROFESSOR:
            return await self.users_manager.change_role_to_professor(id=user.id)
        return await self.users_manager.change_role_except_professors(id=user.id, role=user.role)

    async def delete_user(self, id: UUID, current_user_id: UUID) -> None:
        if current_user_id == id:
            raise CantDeleteOwnProfileError(CANT_DELETE_OWN_PROFILE_ERROR_TEXT)
        await self.users_manager.delete_user(id=id)
        await self.auth_manager.delete_sessions(user_id=id)

    async def reg_professor_application(self, id: UUID, application: ProfessorApplication) -> ApplicationById:
        return await self.users_manager.reg_professor_application(
            id=id,
            name=application.name,
            surname=application.surname,
            patronymic=application.patronymic,
        )

    async def get_professor_applications(self, page: int, size: int) -> ApplicationsList:
        offset = (page - 1) * size
        limit = size
        return await self.users_manager.get_professor_applications(
            offset,
            limit,
        )

    async def change_application_status(self, application: ApplicationChangeStatus) -> None:
        return await self.users_manager.change_application_status(
            id=application.application_id,
            user_id=application.user_id,
            status=application.status,
            comment=application.admin_comment,
        )

    async def get_user_applications(self, id: UUID, page: int, size: int) -> ApplicationsUserList:
        offset = (page - 1) * size
        limit = size
        return await self.users_manager.get_user_applications(id=id, offset=offset, limit=limit)

    def set_user_icon(
            self,
            user: UserVerification,
            icon_upload_file: UploadFile,
    ) -> None:
        if "image" not in icon_upload_file.content_type:
            raise MediaTypeError(
                "Некорректный тип файла!",
            )

        self.users_resources_manager.set_user_icon(
            user.id,
            icon_upload_file,
        )

    async def get_secret_application_link(self) -> SecretApplicationLink:
        if (link := await self.users_manager.get_secret_application_link()) is None:
            raise NotExistingLinkError(NOT_EXISTING_LINK_ERROR_TEXT)
        return SecretApplicationLink(
            secret_part=f""
                        f"{settings.client_settings.professor_application_base_url}/"
                        f"{self.secret_link_handler.get_decoded_link(link.secret_part)}"
        )

    async def set_secret_application_link(self, link_strategy: UpdatedLinkStrategy) -> SecretApplicationLink:
        if not re.fullmatch(ALLOWED_LINK_CHARACTERS, link_strategy.new_link):
            raise UpdatedLinkError(
                UPDATED_LINK_ERROR_TEXT,
            )
        encoded_link = self.secret_link_handler.get_encoded_link(link_strategy.new_link)
        result = await self.users_manager.set_secret_application_link(encoded_link)
        decoded_link = self.secret_link_handler.get_decoded_link(result.secret_part)
        return SecretApplicationLink(secret_part=decoded_link)

    async def verify_secret_link(self, link: str) -> bool:
        if (true_link := await self.users_manager.get_secret_application_link()) is None:
            return False
        return self.secret_link_handler.verify_link(entered_link=link, encoded_true_link=true_link.secret_part)

    async def self_enroll_on_course(
            self,
            user: UserVerification,
            target_user_id: UUID | None,
            course_id: UUID,
    ) -> None:
        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        target_user_id = target_user_id if target_user_id else user.id
        is_user_wants_to_enroll_himself = target_user_id == user.id

        if not is_user_wants_to_enroll_himself:
            requested_user = await self.users_manager.get_user_by_id(target_user_id)
            if requested_user is None:
                raise ObjectMissingError("Пользователя с таким идентификатором не существует!")

        if is_user_wants_to_enroll_himself:
            if user.role == Role.STUDENT:
                if await self.check_course_access(user, course_id) < AccessPermissions.HEADER_ACCESS:
                    raise OperationPermissionError("Пользователь не может записать себя на этот курс!")
        else:
            if user.role == Role.STUDENT:
                raise OperationPermissionError("Пользователь не может записать другого пользователя на курс!")
            if user.role == Role.PROFESSOR and course.professor_id != user.id:
                raise OperationPermissionError("Преподаватель может записать другого студента только на свой курс!")

        if target_user_id == course.professor_id:
            raise ConflictError("Преподаватель курса не может быть записан на него же")

        if await self.courses_manager.check_is_user_enrolled_on_course(
                user.id,
                course_id,
        ):
            raise ConflictError("Пользователь уже записан на данный курс!")

        await self.users_manager.self_enroll_on_course(
            target_user_id,
            course_id,
        )

    async def self_unenroll_from_course(
            self,
            user: UserVerification,
            target_user_id: UUID | None,
            course_id: UUID,
    ) -> None:
        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        target_user_id = target_user_id if target_user_id else user.id
        is_user_wants_to_unenroll_himself = target_user_id == user.id

        if not is_user_wants_to_unenroll_himself:
            requested_user = await self.users_manager.get_user_by_id(target_user_id)
            if requested_user is None:
                raise ObjectMissingError("Пользователя с таким идентификатором не существует!")

        if not is_user_wants_to_unenroll_himself:
            if user.role == Role.STUDENT:
                raise OperationPermissionError("Пользователь не может отписать другого пользователя с курс!")
            if user.role == Role.PROFESSOR and course.professor_id != user.id:
                raise OperationPermissionError("Преподаватель может отписать другого студента только со своего курса!")

        if target_user_id == course.professor_id:
            raise ConflictError("Преподаватель курса не может быть отписан со своего же курса!")

        if not await self.courses_manager.check_is_user_enrolled_on_course(
                target_user_id,
                course_id,
        ):
            raise ConflictError("Пользователь не записан на данный курс!")

        await self.users_manager.self_unenroll_from_course(
            target_user_id,
            course_id,
        )

    async def get_enrolled_users(
            self,
            user: UserVerification | None,
            course_id: UUID,
    ) -> UsersList:
        course = await self.courses_manager.get_course_by_id(course_id)

        if await self.check_course_access(user, course=course) < AccessPermissions.HEADER_ACCESS:
            raise OperationPermissionError("Пользователь не имеет прав доступа к данному курсу!")

        return await self.users_manager.get_enrolled_users(course_id)
