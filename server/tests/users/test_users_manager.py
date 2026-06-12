import uuid

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker

from server.app.api.v1.users.exceptions import UserNotFoundError
from server.app.api.v1.users.users import (
    UserInfo,
    UserProfile,
    UsersList,
    UserVerification,
)
from server.database.models import Users

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


class TestGetAllUsers:
    async def test_returns_paginated_users(self, users_manager, student_factory, professor_factory):
        await student_factory(nickname="a_zebra")
        await student_factory(nickname="m_mouse")
        await professor_factory(nickname="z_alpha")

        result = await users_manager.get_all_users(offset=0, limit=2)
        assert isinstance(result, UsersList)
        assert len(result.root) == 2
        assert result.root[0].nickname < result.root[1].nickname

        result2 = await users_manager.get_all_users(offset=2, limit=2)
        assert len(result2.root) <= 1

    async def test_empty_list_when_no_users(self, users_manager, db_engine):
        async_session = async_sessionmaker(db_engine, expire_on_commit=False)
        async with async_session() as session:
            await session.execute(delete(Users))
            await session.commit()
        result = await users_manager.get_all_users(0, 10)
        assert result.root == []


class TestSearchUsers:
    async def test_search_by_nickname_substring(self, users_manager, student_factory):
        await student_factory(nickname="john_doe")
        await student_factory(nickname="jane_doe")
        await student_factory(nickname="alice_wonder")
        result = await users_manager.search_users("doe", offset=0, limit=10)
        assert len(result.root) == 2
        assert all("doe" in u.nickname for u in result.root)

    async def test_search_case_insensitive(self, users_manager, student_factory):
        await student_factory(nickname="JohnDoe")
        result = await users_manager.search_users("johndoe", offset=0, limit=10)
        assert len(result.root) == 1
        assert result.root[0].nickname == "johndoe"

    async def test_search_no_results(self, users_manager):
        result = await users_manager.search_users("nonexistent", 0, 10)
        assert result.root == []
