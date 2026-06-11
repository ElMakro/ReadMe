import datetime
import uuid

import pytest
from fastapi import HTTPException, status

from server.app.api.v1.users.users import NewUser
from server.database.models import Users

pytestmark = pytest.mark.asyncio


class TestCreateUser:
    async def test_create_user_success(self, auth_manager, db_engine):
        # Подготовка
        new_user = NewUser(
            email="test_create@example.com",
            nickname="testcreate",
            password="hashed_pass"
        )

        created = await auth_manager.create_user(new_user)

        assert created.id is not None
        assert created.nickname == new_user.nickname
        assert created.created_at is not None
        assert created.updated_at is not None
        assert isinstance(created.created_at, datetime.datetime)
        assert isinstance(created.updated_at, datetime.datetime)

        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import async_sessionmaker
        async_session = async_sessionmaker(db_engine, expire_on_commit=False)
        async with async_session() as session:
            stmt = select(Users).where(Users.id == created.id)
            result = await session.execute(stmt)
            db_user = result.scalar_one()
            assert db_user.email == new_user.email
            assert db_user.nickname == new_user.nickname
            assert db_user.created_at is not None
            assert db_user.updated_at is not None

    @pytest.mark.parametrize("existing_nick,new_nick,existing_mail,new_mail", [
        ("nickname", "nickname", "email@example.com", "email2@example.com"),
        ("nickname", "nickname2", "email@example.com", "email@example.com")
    ])
    async def test_create_user_duplicate_fields(self, auth_manager, student_factory,
                                               existing_nick, new_nick, existing_mail, new_mail):
        await student_factory(email=existing_mail, nickname=existing_nick)
        new_user = NewUser(
            email=new_mail,
            nickname=new_nick,
            password="some_password"
        )
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.create_user(new_user)
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT


class TestStoreAndGetToken:
    async def test_store_and_get_token(self, auth_manager, student_factory, redis_client):
        user = await student_factory()
        token = "jwt_token_123"
        session_id = str(uuid.uuid4())

        await auth_manager.store_token(token, user.id, session_id)

        retrieved = await auth_manager.get_token(user.id, session_id)
        assert retrieved == token

        redis_key = f"{user.id}:{session_id}"
        direct_value = await redis_client.get(redis_key)
        assert direct_value == token

    async def test_get_token_nonexistent(self, auth_manager, student_factory):
        user = await student_factory()
        session_id = str(uuid.uuid4())
        result = await auth_manager.get_token(user.id, session_id)
        assert result is None


class TestClearToken:
    async def test_clear_token(self, auth_manager, student_factory, redis_client):
        user = await student_factory()
        token = "some_token"
        session_id = str(uuid.uuid4())
        await auth_manager.store_token(token, user.id, session_id)

        await auth_manager.clear_token(user.id, session_id)

        assert await auth_manager.get_token(user.id, session_id) is None
        redis_key = f"{user.id}:{session_id}"
        assert await redis_client.get(redis_key) is None

    async def test_clear_token_nonexistent(self, auth_manager, student_factory):
        user = await student_factory()
        session_id = str(uuid.uuid4())
        await auth_manager.clear_token(user.id, session_id)


class TestDeleteSessions:
    async def test_delete_sessions_batch(self, auth_manager, student_factory, redis_client):
        user = await student_factory()
        session_ids = [str(uuid.uuid4()) for _ in range(5)]
        for i, sid in enumerate(session_ids):
            await auth_manager.store_token(f"token_{i}", user.id, sid)

        for sid in session_ids:
            assert await auth_manager.get_token(user.id, sid) is not None

        await auth_manager.delete_sessions(user.id, batch_size=2)

        for sid in session_ids:
            assert await auth_manager.get_token(user.id, sid) is None

        keys = await redis_client.keys(f"{user.id}:*")
        assert len(keys) == 0

    async def test_delete_sessions_no_sessions(self, auth_manager, student_factory):
        user = await student_factory()
        await auth_manager.delete_sessions(user.id)

    async def test_delete_sessions_only_this_user(self, auth_manager, student_factory, redis_client):
        user1 = await student_factory()
        user2 = await student_factory()
        await auth_manager.store_token("token1", user1.id, "sess1")
        await auth_manager.store_token("token2", user2.id, "sess2")

        await auth_manager.delete_sessions(user1.id)

        assert await auth_manager.get_token(user1.id, "sess1") is None
        assert await auth_manager.get_token(user2.id, "sess2") == "token2"
