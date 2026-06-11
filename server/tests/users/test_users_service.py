import uuid
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from server.app.api.v1.users.exceptions import (
    UserNotFoundError,
)
from server.app.api.v1.users.users import (
    UserProfile,
    UserUpdatedInfo,
    UserVerification,
)
from server.app.api.v1.users.users_service import UsersService
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
