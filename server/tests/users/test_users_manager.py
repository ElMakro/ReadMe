import uuid

import pytest

from server.app.api.v1.users.exceptions import UserNotFoundError
from server.app.api.v1.users.users import (
    UserInfo,
    UserProfile,
    UserVerification,
)

pytestmark = pytest.mark.asyncio


class TestGetUserProfileInfo:
    async def test_returns_profile_for_existing_user(self, users_manager, student_factory):
        student = await student_factory()
        profile = await users_manager.get_user_profile_info(student.id)
        assert isinstance(profile, UserProfile)
        assert profile.id == student.id
        assert profile.nickname == student.nickname
        assert profile.email == student.email
        assert profile.role == student.role

    async def test_raises_error_for_nonexistent_user(self, users_manager):
        with pytest.raises(UserNotFoundError):
            await users_manager.get_user_profile_info(uuid.uuid4())


class TestGetUserByNickname:
    async def test_returns_user_when_exists(self, users_manager, student_factory):
        student = await student_factory()
        user_info = await users_manager.get_user_by_nickname(student.nickname)
        assert user_info is not None
        assert isinstance(user_info, UserInfo)
        assert user_info.id == student.id
        assert user_info.nickname == student.nickname
        assert user_info.email == student.email
        assert user_info.role == student.role
        assert hasattr(user_info, "password")  # поле пароля должно быть

    async def test_returns_none_when_not_exists(self, users_manager):
        result = await users_manager.get_user_by_nickname("nonexistent_nick")
        assert result is None


class TestGetUserById:
    async def test_returns_verification_when_exists(self, users_manager, student_factory):
        student = await student_factory()
        verification = await users_manager.get_user_by_id(student.id)
        assert isinstance(verification, UserVerification)
        assert verification.id == student.id
        assert verification.nickname == student.nickname
        assert verification.role == student.role
        assert verification.session_id is None

    async def test_returns_none_when_not_exists(self, users_manager):
        result = await users_manager.get_user_by_id(uuid.uuid4())
        assert result is None
