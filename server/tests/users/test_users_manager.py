import uuid

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from server.app.api.v1.users.exceptions import UserMustBeInProfessorsTableError, UserNotFoundError
from server.app.api.v1.users.users import (
    UserInfo,
    UserProfile,
    UsersList,
    UserVerification,
)
from server.database.models import Users
from server.enums.role import Role

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


class TestChangeRoleToProfessor:
    async def test_changes_role_when_user_in_professors_table(self, users_manager, professor_factory,
                                                              student_factory):
        await professor_factory()
        from server.database.models import ProfessorsDetails
        student = await student_factory()
        async with users_manager.db.db_session() as session:
            prof_detail = ProfessorsDetails(id=student.id, name="Test", surname="User",
                                            patronymic=None)
            session.add(prof_detail)
            await session.commit()
        await users_manager.change_role_to_professor(student.id)
        async with users_manager.db.db_session() as session:
            result = await session.execute(select(Users).where(Users.id == student.id))
            user = result.scalar_one()
            assert user.role == Role.PROFESSOR

    async def test_raises_error_if_user_not_in_professors_table(self, users_manager, student_factory):
        student = await student_factory()
        with pytest.raises(UserMustBeInProfessorsTableError):
            await users_manager.change_role_to_professor(student.id)


class TestChangeRoleExceptProfessors:
    async def test_changes_role_to_student(self, users_manager, professor_factory):
        professor = await professor_factory()
        await users_manager.change_role_except_professors(professor.id, Role.STUDENT)
        async with users_manager.db.db_session() as session:
            result = await session.execute(select(Users).where(Users.id == professor.id))
            user = result.scalar_one()
            assert user.role == Role.STUDENT

    async def test_raises_error_when_user_not_found(self, users_manager):
        with pytest.raises(UserNotFoundError):
            await users_manager.change_role_except_professors(uuid.uuid4(), Role.ADMIN)


class TestDeleteUser:
    async def test_deletes_existing_user(self, users_manager, student_factory):
        student = await student_factory()
        await users_manager.delete_user(student.id)
        async with users_manager.db.db_session() as session:
            result = await session.execute(select(Users).where(Users.id == student.id))
            assert result.scalar_one_or_none() is None

    async def test_raises_error_when_user_not_found(self, users_manager):
        with pytest.raises(UserNotFoundError):
            await users_manager.delete_user(uuid.uuid4())
