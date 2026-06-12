import uuid

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from server.app.api.v1.users.exceptions import (
    ApplicationFieldsMismatchError,
    ApplicationRefusedError,
    NotUniqueFieldsError,
    UserMustBeInProfessorsTableError,
    UserNotFoundError,
)
from server.app.api.v1.users.users import (
    ApplicationById,
    SecretApplicationLink,
    UserInfo,
    UserProfile,
    UsersList,
    UserUpdatedInfo,
    UserVerification,
)
from server.database.models import ApplicationLink, ProfessorsApplications, Users
from server.enums.application_status import ApplicationStatus
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


class TestUpdateUserProfile:
    async def test_updates_nickname_and_email(self, users_manager, student_factory):
        student = await student_factory(nickname="old_nick", email="old@example.com")
        updated_info = UserUpdatedInfo(nickname="new_nick", email="new@example.com")
        profile = await users_manager.update_user_profile(student.id, updated_info)
        assert profile.nickname == "new_nick"
        assert profile.email == "new@example.com"
        async with users_manager.db.db_session() as session:
            result = await session.execute(select(Users).where(Users.id == student.id))
            user = result.scalar_one()
            assert user.nickname == "new_nick"
            assert user.email == "new@example.com"

    async def test_raises_not_unique_error_on_duplicate_nickname(self, users_manager, student_factory):
        await student_factory(nickname="unique1")
        student2 = await student_factory(nickname="unique2")
        updated_info = UserUpdatedInfo(nickname="unique1", email="email@example.com")
        with pytest.raises(NotUniqueFieldsError):
            await users_manager.update_user_profile(student2.id, updated_info)

    async def test_raises_not_found_error_when_user_missing(self, users_manager):
        updated_info = UserUpdatedInfo(nickname="user", email="x@x.com")
        with pytest.raises(UserNotFoundError):
            await users_manager.update_user_profile(uuid.uuid4(), updated_info)


class TestRegProfessorApplication:
    async def test_creates_application_successfully(self, users_manager, student_factory):
        student = await student_factory()
        app = await users_manager.reg_professor_application(student.id, "Иван", "Петров", "Сергеевич")
        assert isinstance(app, ApplicationById)
        assert app.id is not None

        async with users_manager.db.db_session() as session:
            result = await session.execute(select(ProfessorsApplications)
                                           .where(ProfessorsApplications.id == app.id))
            db_app = result.scalar_one()
            assert db_app.user_id == student.id
            assert db_app.name == "Иван"
            assert db_app.surname == "Петров"
            assert db_app.patronymic == "Сергеевич"
            assert db_app.status == ApplicationStatus.PENDING

    async def test_raises_error_if_user_already_has_pending_application(self, users_manager, student_factory):
        student = await student_factory()
        await users_manager.reg_professor_application(student.id, "Иван", "Петров", None)
        with pytest.raises(ApplicationRefusedError):
            await users_manager.reg_professor_application(student.id, "Петр", "Сидоров", None)

    async def test_raises_error_if_user_already_professor(self, users_manager, professor_factory):
        professor = await professor_factory()
        with pytest.raises(ApplicationRefusedError):
            await users_manager.reg_professor_application(professor.id, "Иван", "Петров", None)


class TestGetProfessorApplications:
    async def test_returns_pending_applications(self, users_manager, student_factory):
        student1 = await student_factory()
        student2 = await student_factory()
        app1 = await users_manager.reg_professor_application(student1.id, "A", "B", None)
        app2 = await users_manager.reg_professor_application(student2.id, "C", "D", None)

        result = await users_manager.get_professor_applications(0, 10)
        assert len(result.root) == 2
        assert result.root[0].application_id in (app1.id, app2.id)

    async def test_pagination(self, users_manager, student_factory):
        for i in range(5):
            student = await student_factory()
            await users_manager.reg_professor_application(student.id, f"Name{i}", "Surname", None)
        result1 = await users_manager.get_professor_applications(0, 2)
        result2 = await users_manager.get_professor_applications(2, 2)
        assert len(result1.root) == 2
        assert len(result2.root) == 2
        ids1 = {a.application_id for a in result1.root}
        ids2 = {a.application_id for a in result2.root}
        assert ids1.isdisjoint(ids2)


class TestChangeApplicationStatus:
    async def test_changes_status_and_comment(self, users_manager, student_factory):
        student = await student_factory()
        app = await users_manager.reg_professor_application(student.id, "Name", "Surname", None)
        await users_manager.change_application_status(
            app.id, student.id, ApplicationStatus.APPROVED, "Good"
        )
        async with users_manager.db.db_session() as session:
            result = await session.execute(select(ProfessorsApplications)
                                           .where(ProfessorsApplications.id == app.id))
            db_app = result.scalar_one()
            assert db_app.status == ApplicationStatus.APPROVED
            assert db_app.admin_comment == "Good"

    async def test_raises_error_if_ids_mismatch(self, users_manager, student_factory):
        student = await student_factory()
        app = await users_manager.reg_professor_application(student.id, "Name", "Surname", None)
        other_id = uuid.uuid4()
        with pytest.raises(ApplicationFieldsMismatchError):
            await users_manager.change_application_status(
                app.id, other_id, ApplicationStatus.APPROVED, ""
            )


class TestGetUserApplications:
    async def test_returns_applications_for_user(self, users_manager, student_factory):
        student = await student_factory()
        app1 = await users_manager.reg_professor_application(student.id, "Name1", "Surname1", None)
        await users_manager.change_application_status(
            id=app1.id,
            user_id=student.id,
            status=ApplicationStatus.REJECTED,
            comment="Отклонено для теста"
        )
        app2 = await users_manager.reg_professor_application(student.id, "Name2", "Surname2", None)
        result = await users_manager.get_user_applications(student.id, offset=0, limit=10)

        assert len(result.root) == 2
        apps_by_id = {app.application_id: app for app in result.root}
        assert apps_by_id[app1.id].status == ApplicationStatus.REJECTED
        assert apps_by_id[app2.id].status == ApplicationStatus.PENDING

    async def test_pagination(self, users_manager, student_factory):
        student = await student_factory()
        for i in range(5):
            app = await users_manager.reg_professor_application(student.id, f"Name{i}", "Surname", None)
            await users_manager.change_application_status(
                id=app.id,
                user_id=student.id,
                status=ApplicationStatus.REJECTED,
                comment="Отклонено для теста"
            )
        result1 = await users_manager.get_user_applications(student.id, 0, 2)
        result2 = await users_manager.get_user_applications(student.id, 2, 2)
        assert len(result1.root) == 2
        assert len(result2.root) == 2


class TestGetSecretApplicationLink:
    async def test_returns_none_when_no_link(self, users_manager):
        async with users_manager.db.db_session() as session:
            await session.execute(delete(ApplicationLink))
            await session.commit()
        link = await users_manager.get_secret_application_link()
        assert link is None

    async def test_returns_link_when_exists(self, users_manager):
        await users_manager.set_secret_application_link("test_secret")
        retrieved = await users_manager.get_secret_application_link()
        assert isinstance(retrieved, SecretApplicationLink)
        assert retrieved.secret_part == "test_secret"


class TestSetSecretApplicationLink:
    async def test_creates_new_link_when_none(self, users_manager):
        async with users_manager.db.db_session() as session:
            await session.execute(delete(ApplicationLink))
            await session.commit()
        result = await users_manager.set_secret_application_link("new_link_value")
        assert isinstance(result, SecretApplicationLink)
        assert result.secret_part == "new_link_value"

    async def test_updates_existing_link(self, users_manager):
        await users_manager.set_secret_application_link("first")
        updated = await users_manager.set_secret_application_link("second")
        assert updated.secret_part == "second"
        async with users_manager.db.db_session() as session:
            result = await session.execute(select(ApplicationLink))
            links = result.scalars().all()
            assert len(links) == 1
            assert links[0].secret_part == "second"
