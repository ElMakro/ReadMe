import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Response, status
from pytest_mock import MockerFixture

from server.app.api.v1.auth.auth_service import AuthService
from server.app.api.v1.common_schemas import MessageResponse
from server.app.api.v1.users.users import (
    UserAuthentication,
    UserRegistration,
    UserVerification,
)
from server.config.settings import settings
from server.enums.role import Role

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_auth_manager(mocker: MockerFixture):
    return mocker.AsyncMock()

@pytest.fixture
def mock_auth_handler(mocker: MockerFixture):
    handler = mocker.AsyncMock()
    handler.get_hashed_password = mocker.AsyncMock()
    handler.verify_password = mocker.AsyncMock()
    handler.create_token = mocker.AsyncMock()
    return handler

@pytest.fixture
def mock_users_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.get_user_by_nickname = mocker.AsyncMock()
    return manager

@pytest.fixture
def mock_users_resources_manager(mocker: MockerFixture):
    manager = mocker.MagicMock()
    manager.create_user = mocker.MagicMock()
    return manager

@pytest.fixture
def auth_service(
    mock_auth_manager,
    mock_auth_handler,
    mock_users_manager,
    mock_users_resources_manager,
) -> AuthService:
    return AuthService(
        auth_manager=mock_auth_manager,
        auth_handler=mock_auth_handler,
        users_manager=mock_users_manager,
        users_resources_manager=mock_users_resources_manager,
    )


class TestRegisterUser:
    async def test_register_user_success(
        self,
        auth_service: AuthService,
        mock_auth_handler,
        mock_auth_manager,
        mock_users_resources_manager,
    ):
        user_reg = UserRegistration(
            email="test@example.com",
            nickname="testuser",
            password="plainpass"
        )
        hashed_password = "hashed_pass123"
        expected_created_user = MagicMock(id=uuid.uuid4(), email=user_reg.email, nickname=user_reg.nickname)
        mock_auth_handler.get_hashed_password.return_value = hashed_password
        mock_auth_manager.create_user.return_value = expected_created_user

        result = await auth_service.register_user(user_reg)

        mock_auth_handler.get_hashed_password.assert_awaited_once_with("plainpass")
        mock_auth_manager.create_user.assert_awaited_once()
        call_args = mock_auth_manager.create_user.call_args[1]
        assert call_args["user"].email == user_reg.email
        assert call_args["user"].nickname == user_reg.nickname
        assert call_args["user"].password == hashed_password
        mock_users_resources_manager.create_user.assert_called_once_with(expected_created_user)
        assert result == expected_created_user


class TestLoginUser:
    async def test_login_user_success(
        self,
        auth_service: AuthService,
        mock_users_manager,
        mock_auth_handler,
        mock_auth_manager,
    ):
        id_ = uuid.uuid4()
        password = "secret_password"
        hashed_password = "hashed_secret_password"
        nickname = "testuser"
        session = "session_123"
        user_auth = UserAuthentication(nickname=nickname, password=password)
        existing_user = MagicMock(id=id_, password=hashed_password)
        mock_users_manager.get_user_by_nickname.return_value = existing_user
        mock_auth_handler.verify_password.return_value = True
        mock_auth_handler.create_token.return_value = ("jwt_token", session)
        response = Response()

        result = await auth_service.login_user(user_auth, response)

        mock_users_manager.get_user_by_nickname.assert_awaited_once_with(nickname)
        mock_auth_handler.verify_password.assert_awaited_once_with(
            entered_password=password,
            hashed_password=hashed_password
        )
        mock_auth_handler.create_token.assert_awaited_once_with(id_)
        mock_auth_manager.store_token.assert_awaited_once_with(
            token="jwt_token",
            user_id=id_,
            session_id=session
        )
        cookie_header = response.headers.get("set-cookie", "")
        assert "Authorization=jwt_token" in cookie_header
        assert "HttpOnly" in cookie_header
        assert f"Max-Age={settings.token_expire}" in cookie_header
        assert result == MessageResponse(message="Успешный вход", details=None)

    async def test_login_user_user_not_found(
        self,
        auth_service: AuthService,
        mock_users_manager,
        mock_auth_handler,
    ):
        user_auth = UserAuthentication(nickname="unknown", password="secret_password")
        mock_users_manager.get_user_by_nickname.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login_user(user_auth, Response())

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Неверное имя пользователя или пароль."
        mock_auth_handler.verify_password.assert_not_awaited()
        mock_auth_handler.create_token.assert_not_awaited()

    async def test_login_user_wrong_password(
        self,
        auth_service: AuthService,
        mock_users_manager,
        mock_auth_handler,
    ):
        user_auth = UserAuthentication(nickname="testuser", password="wrong_password")
        existing_user = MagicMock(password="correct_hash")
        mock_users_manager.get_user_by_nickname.return_value = existing_user
        mock_auth_handler.verify_password.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login_user(user_auth, Response())

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Неверное имя пользователя или пароль."
        mock_auth_handler.verify_password.assert_awaited_once()
        mock_auth_handler.create_token.assert_not_awaited()


class TestLogoutUser:
    async def test_logout_user_success(
        self,
        auth_service: AuthService,
        mock_auth_manager,
    ):
        id_ = uuid.uuid4()
        nickname = "testuser"
        session = "session_123"
        user_verif = UserVerification(id=id_, nickname=nickname, role=Role.STUDENT, session_id=session)
        response = Response()

        result = await auth_service.logout_user(user_verif, response)

        mock_auth_manager.clear_token.assert_awaited_once_with(
            user_id=id_,
            session_id=session
        )
        cookie_header = response.headers.get("set-cookie", "")
        assert "Authorization=;" in cookie_header or "Authorization=" in cookie_header
        assert "Max-Age=0" in cookie_header
        assert result == MessageResponse(message="Успешный выход", details=None)
