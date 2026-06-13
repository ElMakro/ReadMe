import re
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import UploadFile
from pytest_mock import MockerFixture

from server.app.api.v1.common_schemas import (
    CANT_CHANGE_OWN_ROLE_ERROR_TEXT,
    CANT_DELETE_OWN_PROFILE_ERROR_TEXT,
    NOT_EXISTING_LINK_ERROR_TEXT,
    UPDATED_LINK_ERROR_TEXT,
)
from server.app.api.v1.exceptions import (
    BadRequestError,
    ConflictError,
    MediaTypeError,
    ObjectMissingError,
    OperationPermissionError,
)
from server.app.api.v1.notes.exceptions import CantChangeOwnRoleError, CantDeleteOwnProfileError
from server.app.api.v1.users.exceptions import (
    NotExistingLinkError,
    UpdatedLinkError,
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
from server.app.common_dependencies.secret_link_strategies import CustomLinkStrategy
from server.config.settings import settings
from server.enums.access_permissions import AccessPermissions
from server.enums.application_status import ApplicationStatus
from server.enums.role import Role

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_auth_manager(mocker: MockerFixture):
    return mocker.AsyncMock()

@pytest.fixture
def mock_users_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.get_user_profile_info = mocker.AsyncMock()
    manager.update_user_profile = mocker.AsyncMock()
    manager.get_all_users = mocker.AsyncMock()
    manager.search_users = mocker.AsyncMock()
    manager.change_role_to_professor = mocker.AsyncMock()
    manager.change_role_except_professors = mocker.AsyncMock()
    manager.delete_user = mocker.AsyncMock()
    manager.reg_professor_application = mocker.AsyncMock()
    manager.get_professor_applications = mocker.AsyncMock()
    manager.change_application_status = mocker.AsyncMock()
    manager.get_user_applications = mocker.AsyncMock()
    manager.get_secret_application_link = mocker.AsyncMock()
    manager.set_secret_application_link = mocker.AsyncMock()
    manager.get_user_by_id = mocker.AsyncMock()
    manager.enroll = mocker.AsyncMock()
    manager.unenroll = mocker.AsyncMock()
    manager.get_enrolled_users = mocker.AsyncMock()
    return manager

@pytest.fixture
def mock_courses_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.get_course_by_id = mocker.AsyncMock()
    manager.check_is_user_enrolled_on_course = mocker.AsyncMock()
    return manager

@pytest.fixture
def mock_users_resources_manager(mocker: MockerFixture):
    manager = mocker.MagicMock()  # синхронный
    manager.set_user_icon = mocker.MagicMock()
    return manager

@pytest.fixture
def mock_secret_link_handler(mocker: MockerFixture):
    handler = mocker.MagicMock()
    handler.get_decoded_link = mocker.MagicMock()
    handler.get_encoded_link = mocker.MagicMock()
    handler.verify_link = mocker.MagicMock()
    return handler

@pytest.fixture
def users_service(
    mock_auth_manager,
    mock_users_manager,
    mock_courses_manager,
    mock_users_resources_manager,
    mock_secret_link_handler,
) -> UsersService:
    return UsersService(
        auth_manager=mock_auth_manager,
        users_manager=mock_users_manager,
        courses_manager=mock_courses_manager,
        users_resources_manager=mock_users_resources_manager,
        secret_link_handler=mock_secret_link_handler,
    )


class TestGetInfoForUserProfile:
    @pytest.mark.parametrize("role", [
        Role.STUDENT,
        Role.PROFESSOR,
        Role.ADMIN
    ])
    async def test_returns_user_profile(self, users_service, mock_users_manager, role):
        user = UserVerification(id=uuid.uuid4(), nickname="some_nick",
                                session_id="session_1", role=role)
        expected_profile = MagicMock(spec=UserProfile)
        mock_users_manager.get_user_profile_info.return_value = expected_profile

        result = await users_service.get_info_for_user_profile(user)

        mock_users_manager.get_user_profile_info.assert_awaited_once_with(user_id=user.id)
        assert result == expected_profile


class TestUpdateUserProfile:
    async def test_updates_profile(self, users_service, mock_users_manager):
        user_id = uuid.uuid4()
        updated_info = UserUpdatedInfo(nickname="new_nick", email="email@example.com")
        expected_profile = MagicMock(spec=UserProfile)
        mock_users_manager.update_user_profile.return_value = expected_profile

        result = await users_service.update_user_profile(user_id, updated_info)

        mock_users_manager.update_user_profile.assert_awaited_once_with(user_id=user_id, updated_info=updated_info)
        assert result == expected_profile

    async def test_raises_exception_when_user_not_found(self, users_service, mock_users_manager):
        user_id = uuid.uuid4()
        updated_info = UserUpdatedInfo(nickname="new_nick", email="email@example.com")
        mock_users_manager.update_user_profile.side_effect = UserNotFoundError()

        with pytest.raises(UserNotFoundError):
            await users_service.update_user_profile(user_id, updated_info)


class TestCheckCourseAccess:
    async def test_admin_gets_edit_access(self, users_service, mock_courses_manager):
        user = UserVerification(id=uuid.uuid4(), role=Role.ADMIN, session_id="s", nickname="admin")
        result = await users_service.check_course_access(user)
        assert result == AccessPermissions.EDIT_ACCESS

    async def test_professor_gets_edit_access_for_own_course(self, users_service, mock_courses_manager):
        user = UserVerification(id=uuid.uuid4(), role=Role.PROFESSOR, session_id="s", nickname="prof")
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=user.id, is_content_public=False, is_public=False)
        mock_courses_manager.get_course_by_id.return_value = course
        result = await users_service.check_course_access(user, course_id=course_id)
        assert result == AccessPermissions.EDIT_ACCESS
        mock_courses_manager.get_course_by_id.assert_awaited_once_with(course_id)

    async def test_content_access_when_course_content_public(self, users_service, mock_courses_manager):
        user = UserVerification(id=uuid.uuid4(), role=Role.STUDENT, session_id="s", nickname="student")
        course = MagicMock(
            id=uuid.uuid4(),
            is_content_public=True,
            professor_id=uuid.uuid4(),
            is_public=False,
        )
        result = await users_service.check_course_access(user, course=course)
        assert result == AccessPermissions.CONTENT_ACCESS
        mock_courses_manager.get_course_by_id.assert_not_called()

    async def test_content_access_when_user_enrolled(self, users_service, mock_courses_manager):
        user = UserVerification(id=uuid.uuid4(), role=Role.STUDENT, session_id="s", nickname="student")
        course_id = uuid.uuid4()
        course = MagicMock(
            id=course_id,
            is_content_public=False,
            is_public=False,
            professor_id=uuid.uuid4()
        )
        mock_courses_manager.get_course_by_id.return_value = course
        mock_courses_manager.check_is_user_enrolled_on_course.return_value = True
        result = await users_service.check_course_access(user, course_id=course_id)
        assert result == AccessPermissions.CONTENT_ACCESS
        mock_courses_manager.check_is_user_enrolled_on_course.assert_awaited_once_with(user.id, course_id)

    async def test_header_access_when_course_public(self, users_service, mock_courses_manager):
        user = UserVerification(id=uuid.uuid4(), role=Role.STUDENT, session_id="s", nickname="student")
        course = MagicMock(
            id=uuid.uuid4(),
            is_content_public=False,
            is_public=True,
            professor_id=uuid.uuid4(),
        )
        mock_courses_manager.check_is_user_enrolled_on_course.return_value = False
        result = await users_service.check_course_access(user, course=course)
        assert result == AccessPermissions.HEADER_ACCESS

    async def test_no_access_for_anonymous_on_private_course(self, users_service, mock_courses_manager):
        course_id = uuid.uuid4()
        course = MagicMock(
            id=course_id,
            is_content_public=False,
            is_public=False,
            professor_id=uuid.uuid4()
        )
        mock_courses_manager.get_course_by_id.return_value = course
        result = await users_service.check_course_access(None, course_id=course_id)
        assert result == AccessPermissions.NO_ACCESS

    async def test_raises_value_error_when_no_course_and_no_id(self, users_service):
        with pytest.raises(ValueError, match="Либо курс, либо его идентификатор должны быть переданы!"):
            await users_service.check_course_access(None)

class TestGetAllUsers:
    async def test_pagination_converted_correctly(self, users_service, mock_users_manager):
        mock_users_manager.get_all_users.return_value = MagicMock(spec=UsersList)

        result = await users_service.get_all_users(page=3, size=9)

        mock_users_manager.get_all_users.assert_awaited_once_with(18, 9)
        assert isinstance(result, UsersList)


class TestSearchUsers:
    async def test_search_pagination(self, users_service, mock_users_manager):
        mock_users_manager.search_users.return_value = MagicMock(spec=UsersList)

        result = await users_service.search_users(pattern="test", page=2, size=15)

        mock_users_manager.search_users.assert_awaited_once_with("test", 15, 15)
        assert isinstance(result, UsersList)


class TestChangeRole:
    async def test_cannot_change_own_role(self, users_service):
        user_id = uuid.uuid4()
        user_with_role = UserWithRole(id=user_id, role=Role.STUDENT)

        with pytest.raises(CantChangeOwnRoleError) as exc:
            await users_service.change_role(user_with_role, current_user_id=user_id)
        assert CANT_CHANGE_OWN_ROLE_ERROR_TEXT in str(exc.value)

    async def test_change_to_professor_calls_correct_manager_method(self, users_service, mock_users_manager):
        target_id = uuid.uuid4()
        user_with_role = UserWithRole(id=target_id, role=Role.PROFESSOR)

        await users_service.change_role(user_with_role, current_user_id=uuid.uuid4())

        mock_users_manager.change_role_to_professor.assert_awaited_once_with(id=target_id)
        mock_users_manager.change_role_except_professors.assert_not_called()

    async def test_change_to_student_calls_except_professors(self, users_service, mock_users_manager):
        target_id = uuid.uuid4()
        user_with_role = UserWithRole(id=target_id, role=Role.STUDENT)

        await users_service.change_role(user_with_role, current_user_id=uuid.uuid4())

        mock_users_manager.change_role_except_professors.assert_awaited_once_with(id=target_id,
                                                                                  role=Role.STUDENT)
        mock_users_manager.change_role_to_professor.assert_not_called()


class TestDeleteUser:
    async def test_cannot_delete_self(self, users_service):
        user_id = uuid.uuid4()
        with pytest.raises(CantDeleteOwnProfileError) as exc:
            await users_service.delete_user(id=user_id, current_user_id=user_id)
        assert CANT_DELETE_OWN_PROFILE_ERROR_TEXT in str(exc.value)

    async def test_delete_other_user_clears_sessions(self, users_service, mock_users_manager, mock_auth_manager):
        target_id = uuid.uuid4()
        current_id = uuid.uuid4()

        await users_service.delete_user(id=target_id, current_user_id=current_id)

        mock_users_manager.delete_user.assert_awaited_once_with(id=target_id)
        mock_auth_manager.delete_sessions.assert_awaited_once_with(user_id=target_id)


class TestRegProfessorApplication:
    async def test_registers_application(self, users_service, mock_users_manager):
        user_id = uuid.uuid4()
        application = ProfessorApplication(name="Иван", surname="Петров", patronymic="Сергеевич")
        expected = MagicMock(spec=ApplicationById)
        mock_users_manager.reg_professor_application.return_value = expected

        result = await users_service.reg_professor_application(user_id, application)

        mock_users_manager.reg_professor_application.assert_awaited_once_with(
            id=user_id,
            name=application.name,
            surname=application.surname,
            patronymic=application.patronymic,
        )
        assert result == expected


class TestGetProfessorApplications:
    async def test_pagination(self, users_service, mock_users_manager):
        mock_users_manager.get_professor_applications.return_value = MagicMock(spec=ApplicationsList)

        result = await users_service.get_professor_applications(page=2, size=25)

        mock_users_manager.get_professor_applications.assert_awaited_once_with(25, 25)
        assert isinstance(result, ApplicationsList)


class TestChangeApplicationStatus:
    @pytest.mark.parametrize("application_status,comment", [
        (ApplicationStatus.APPROVED, "Ok"),
        (ApplicationStatus.REJECTED, "Rejected"),
        (ApplicationStatus.PENDING, None),
    ])
    async def test_changes_status(self, users_service, mock_users_manager, application_status, comment):
        application = ApplicationChangeStatus(
            application_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            status=application_status,
            admin_comment=comment,
        )
        await users_service.change_application_status(application)
        mock_users_manager.change_application_status.assert_awaited_once_with(
            id=application.application_id,
            user_id=application.user_id,
            status=application.status,
            comment=application.admin_comment,
        )


class TestGetUserApplications:
    async def test_pagination(self, users_service, mock_users_manager):
        user_id = uuid.uuid4()
        mock_users_manager.get_user_applications.return_value = MagicMock(spec=ApplicationsUserList)

        result = await users_service.get_user_applications(user_id, page=3, size=10)

        mock_users_manager.get_user_applications.assert_awaited_once_with(id=user_id, offset=20, limit=10)
        assert isinstance(result, ApplicationsUserList)


class TestSetUserIcon:
    async def test_valid_image_passes(self, users_service, mock_users_resources_manager):
        user = UserVerification(id=uuid.uuid4(), nickname="user", session_id="s", role=Role.STUDENT)
        upload_file = MagicMock(spec=UploadFile)
        upload_file.content_type = "image/jpeg"

        users_service.set_user_icon(user, upload_file)

        mock_users_resources_manager.set_user_icon.assert_called_once_with(user.id, upload_file)

    async def test_invalid_content_type_raises_media_type_error(self, users_service):
        user = UserVerification(id=uuid.uuid4(), nickname="user", session_id="s", role=Role.STUDENT)
        upload_file = MagicMock(spec=UploadFile)
        upload_file.content_type = "application/pdf"

        with pytest.raises(MediaTypeError, match="Некорректный тип файла!"):
            users_service.set_user_icon(user, upload_file)

    async def test_value_error_from_manager_raises_bad_request(self, users_service, mock_users_resources_manager):
        user = UserVerification(id=uuid.uuid4(), nickname="user", session_id="s", role=Role.STUDENT)
        upload_file = MagicMock(spec=UploadFile)
        upload_file.content_type = "image/png"
        mock_users_resources_manager.set_user_icon.side_effect = ValueError("some error")

        with pytest.raises(BadRequestError, match="some error"):
            users_service.set_user_icon(user, upload_file)


class TestGetSecretApplicationLink:
    async def test_returns_link_when_exists(self, users_service, mock_users_manager, mock_secret_link_handler):
        mock_link = MagicMock(secret_part="encoded123")
        mock_users_manager.get_secret_application_link.return_value = mock_link
        mock_secret_link_handler.get_decoded_link.return_value = "decoded_link"

        result = await users_service.get_secret_application_link()

        expected_secret_part = f"{settings.client_settings.professor_application_base_url}/decoded_link"
        assert result.secret_part == expected_secret_part
        mock_secret_link_handler.get_decoded_link.assert_called_once_with("encoded123")

    async def test_raises_not_existing_error_when_no_link(self, users_service, mock_users_manager):
        mock_users_manager.get_secret_application_link.return_value = None

        with pytest.raises(NotExistingLinkError, match=NOT_EXISTING_LINK_ERROR_TEXT):
            await users_service.get_secret_application_link()


class TestSetSecretApplicationLink:
    async def test_sets_link_successfully(self, users_service, mock_users_manager, mock_secret_link_handler):
        new_link_str = "valid_link"
        link_strategy = CustomLinkStrategy(new_link_str)
        mock_secret_link_handler.get_encoded_link.return_value = "encoded"
        mock_secret_link_handler.get_decoded_link.return_value = "decoded"
        mock_result = MagicMock(secret_part="encoded")
        mock_users_manager.set_secret_application_link.return_value = mock_result

        result = await users_service.set_secret_application_link(link_strategy)

        mock_secret_link_handler.get_encoded_link.assert_called_once_with(new_link_str)
        mock_users_manager.set_secret_application_link.assert_awaited_once_with("encoded")
        mock_secret_link_handler.get_decoded_link.assert_called_once_with("encoded")
        assert result.secret_part == "decoded"

    async def test_raises_error_when_link_does_not_match_pattern(self, users_service):
        link_strategy = CustomLinkStrategy("invalid@!")
        with pytest.raises(UpdatedLinkError, match=re.escape(UPDATED_LINK_ERROR_TEXT)):
            await users_service.set_secret_application_link(link_strategy)


class TestVerifySecretLink:
    async def test_returns_true_when_matches(self, users_service, mock_users_manager, mock_secret_link_handler):
        mock_users_manager.get_secret_application_link.return_value = MagicMock(secret_part="encoded")
        mock_secret_link_handler.verify_link.return_value = True

        result = await users_service.verify_secret_link("entered")

        assert result is True
        mock_secret_link_handler.verify_link.assert_called_once_with(entered_link="entered",
                                                                     encoded_true_link="encoded")

    async def test_returns_false_when_no_link_in_db(self, users_service, mock_users_manager):
        mock_users_manager.get_secret_application_link.return_value = None

        result = await users_service.verify_secret_link("anything")
        assert result is False

    async def test_returns_false_when_verification_fails(self, users_service, mock_users_manager,
                                                         mock_secret_link_handler):
        mock_users_manager.get_secret_application_link.return_value = MagicMock(secret_part="encoded")
        mock_secret_link_handler.verify_link.return_value = False

        result = await users_service.verify_secret_link("wrong")
        assert result is False


class TestEnroll:
    async def test_student_enrolls_self_on_public_course(self, users_service, mock_courses_manager,
                                                         mock_users_manager):
        user = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.STUDENT, session_id="s")
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=uuid.uuid4(), is_public=True, is_content_public=False)
        mock_courses_manager.get_course_by_id.return_value = course
        mock_courses_manager.check_is_user_enrolled_on_course.return_value = False

        await users_service.enroll(user, target_user_id=None, course_id=course_id)

        mock_users_manager.enroll.assert_awaited_once_with(user.id, course_id)

    async def test_student_cannot_enroll_another_user(self, users_service, mock_courses_manager):
        user = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.STUDENT, session_id="s")
        other_id = uuid.uuid4()
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=uuid.uuid4())
        mock_courses_manager.get_course_by_id.return_value = course

        with pytest.raises(OperationPermissionError):
            await users_service.enroll(user, target_user_id=other_id, course_id=course_id)

    async def test_professor_can_enroll_student_on_own_course(self, users_service, mock_courses_manager,
                                                              mock_users_manager):
        professor = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.PROFESSOR, session_id="s")
        student_id = uuid.uuid4()
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=professor.id, is_public=False)
        mock_courses_manager.get_course_by_id.return_value = course
        mock_users_manager.get_user_by_id.return_value = MagicMock(id=student_id)
        mock_courses_manager.check_is_user_enrolled_on_course.return_value = False

        await users_service.enroll(professor, target_user_id=student_id, course_id=course_id)

        mock_users_manager.enroll.assert_awaited_once_with(student_id, course_id)

    async def test_professor_cannot_enroll_on_others_course(self, users_service, mock_courses_manager,
                                                            mock_users_manager):
        professor = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.PROFESSOR, session_id="s")
        student_id = uuid.uuid4()
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=uuid.uuid4())  # not his course
        mock_courses_manager.get_course_by_id.return_value = course
        mock_users_manager.get_user_by_id.return_value = MagicMock(id=student_id)

        with pytest.raises(OperationPermissionError):
            await users_service.enroll(professor, target_user_id=student_id, course_id=course_id)

    async def test_cannot_enroll_course_professor(self, users_service, mock_courses_manager):
        user = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.STUDENT, session_id="s")
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=user.id)
        mock_courses_manager.get_course_by_id.return_value = course

        with pytest.raises(ConflictError):
            await users_service.enroll(user, target_user_id=None, course_id=course_id)

    async def test_cannot_enroll_if_already_enrolled(self, users_service, mock_courses_manager):
        user = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.STUDENT, session_id="s")
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=uuid.uuid4())
        mock_courses_manager.get_course_by_id.return_value = course
        mock_courses_manager.check_is_user_enrolled_on_course.return_value = True

        with pytest.raises(ConflictError):
            await users_service.enroll(user, target_user_id=None, course_id=course_id)

    async def test_enroll_student_successfully_enrolls_self(self, users_service, mocker):
        current_user = UserVerification(id=uuid.uuid4(), role=Role.STUDENT, nickname="student", session_id="sess")
        requested_user_id = current_user.id
        course_id = uuid.uuid4()
        users_service.courses_manager.get_course_by_id = mocker.AsyncMock(
            return_value=MagicMock(id=course_id, professor_id=uuid.uuid4()))
        users_service.users_manager.get_user_by_id = mocker.AsyncMock(return_value=MagicMock(id=requested_user_id))
        mocker.patch.object(users_service, 'check_course_access', return_value=AccessPermissions.HEADER_ACCESS)
        users_service.courses_manager.check_is_user_enrolled_on_course = mocker.AsyncMock(return_value=False)
        users_service.users_manager.enroll = mocker.AsyncMock()

        await users_service.enroll(current_user, requested_user_id, course_id)
        users_service.users_manager.enroll.assert_awaited_once_with(requested_user_id, course_id)

    async def test_enroll_raises_error_if_requested_user_not_found(self, users_service, mocker):
        current_user = UserVerification(id=uuid.uuid4(), role=Role.PROFESSOR, nickname="prof", session_id="sess")
        requested_user_id = uuid.uuid4()
        users_service.users_manager.get_user_by_id = mocker.AsyncMock(return_value=None)
        users_service.courses_manager.get_course_by_id = mocker.AsyncMock(return_value=MagicMock())

        with pytest.raises(ObjectMissingError):
            await users_service.enroll(current_user, requested_user_id, uuid.uuid4())

    async def test_enroll_student_without_access_raises_error(self, users_service, mocker):
        current_user = UserVerification(id=uuid.uuid4(), role=Role.STUDENT, nickname="student", session_id="sess")
        requested_user_id = current_user.id
        course_id = uuid.uuid4()
        users_service.users_manager.get_user_by_id = mocker.AsyncMock(return_value=MagicMock(id=requested_user_id))
        users_service.courses_manager.get_course_by_id = mocker.AsyncMock(return_value=MagicMock(id=course_id))
        mocker.patch.object(users_service, 'check_course_access', return_value=AccessPermissions.NO_ACCESS)

        with pytest.raises(OperationPermissionError):
            await users_service.enroll(current_user, requested_user_id, course_id)


class TestUnenroll:
    async def test_student_unenrolls_self(self, users_service, mock_courses_manager, mock_users_manager):
        user = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.STUDENT, session_id="s")
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=uuid.uuid4())
        mock_courses_manager.get_course_by_id.return_value = course
        mock_courses_manager.check_is_user_enrolled_on_course.return_value = True

        await users_service.unenroll(user, target_user_id=None, course_id=course_id)

        mock_users_manager.unenroll.assert_awaited_once_with(user.id, course_id)

    async def test_student_cannot_unenroll_another(self, users_service, mock_courses_manager):
        user = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.STUDENT, session_id="s")
        other_id = uuid.uuid4()
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=uuid.uuid4())
        mock_courses_manager.get_course_by_id.return_value = course

        with pytest.raises(OperationPermissionError):
            await users_service.unenroll(user, target_user_id=other_id, course_id=course_id)

    async def test_professor_can_unenroll_student_from_own_course(self, users_service, mock_courses_manager,
                                                                  mock_users_manager):
        professor = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.PROFESSOR, session_id="s")
        student_id = uuid.uuid4()
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=professor.id)
        mock_courses_manager.get_course_by_id.return_value = course
        mock_users_manager.get_user_by_id.return_value = MagicMock(id=student_id)
        mock_courses_manager.check_is_user_enrolled_on_course.return_value = True

        await users_service.unenroll(professor, target_user_id=student_id, course_id=course_id)

        mock_users_manager.unenroll.assert_awaited_once_with(student_id, course_id)

    async def test_cannot_unenroll_course_professor(self, users_service, mock_courses_manager):
        user = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.STUDENT, session_id="s")
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=user.id)
        mock_courses_manager.get_course_by_id.return_value = course

        with pytest.raises(ConflictError):
            await users_service.unenroll(user, target_user_id=None, course_id=course_id)

    async def test_cannot_unenroll_if_not_enrolled(self, users_service, mock_courses_manager):
        user = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.STUDENT, session_id="s")
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=uuid.uuid4())
        mock_courses_manager.get_course_by_id.return_value = course
        mock_courses_manager.check_is_user_enrolled_on_course.return_value = False

        with pytest.raises(ConflictError):
            await users_service.unenroll(user, target_user_id=None, course_id=course_id)

    async def test_unenroll_raises_error_if_requested_user_not_found(self, users_service, mocker):
        current_user = UserVerification(id=uuid.uuid4(), role=Role.PROFESSOR, nickname="prof", session_id="sess")
        requested_user_id = uuid.uuid4()
        users_service.users_manager.get_user_by_id = mocker.AsyncMock(return_value=None)
        users_service.courses_manager.get_course_by_id = mocker.AsyncMock(return_value=MagicMock())

        with pytest.raises(ObjectMissingError):
            await users_service.unenroll(current_user, requested_user_id, uuid.uuid4())

    async def test_unenroll_professor_not_own_course_raises_error(self, users_service, mocker):
        current_user = UserVerification(id=uuid.uuid4(), role=Role.PROFESSOR, nickname="prof", session_id="sess")
        requested_user_id = uuid.uuid4()
        course_id = uuid.uuid4()
        course = MagicMock(id=course_id, professor_id=uuid.uuid4())
        users_service.users_manager.get_user_by_id = mocker.AsyncMock(return_value=MagicMock(id=requested_user_id))
        users_service.courses_manager.get_course_by_id = mocker.AsyncMock(return_value=course)

        with pytest.raises(OperationPermissionError):
            await users_service.unenroll(current_user, requested_user_id, course_id)


class TestGetEnrolledUsers:
    async def test_returns_users_list_when_access_granted(self, users_service, mock_courses_manager,
                                                          mock_users_manager):
        user = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.PROFESSOR, session_id="s")
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=user.id, is_public=False)
        mock_courses_manager.get_course_by_id.return_value = course
        expected = MagicMock(spec=UsersList)
        mock_users_manager.get_enrolled_users.return_value = expected

        result = await users_service.get_enrolled_users(user, course_id)

        assert result == expected
        mock_users_manager.get_enrolled_users.assert_awaited_once_with(course_id)

    async def test_raises_error_when_no_access(self, users_service, mock_courses_manager):
        user = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.STUDENT, session_id="s")
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=uuid.uuid4(), is_public=False, is_content_public=False)
        mock_courses_manager.get_course_by_id.return_value = course
        mock_courses_manager.check_is_user_enrolled_on_course.return_value = False

        with pytest.raises(OperationPermissionError):
            await users_service.get_enrolled_users(user, course_id)
