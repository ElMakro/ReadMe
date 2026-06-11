import os
import sys
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from alembic.config import Config
from alembic import command
import asyncio


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from fastapi.testclient import TestClient
from server.main import app
from server.config.db_dependency import DBDependency


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:18") as postgres:
        sync_url = postgres.get_connection_url()
        async_url = sync_url.replace("+psycopg2", "+asyncpg")

        alembic_ini_path = os.path.join(project_root, "alembic.ini")
        alembic_cfg = Config(alembic_ini_path)

        script_location = os.path.join(project_root, "server", "database", "alembic")
        alembic_cfg.set_main_option("script_location", script_location)
        alembic_cfg.set_main_option("sqlalchemy.url", async_url)

        command.upgrade(alembic_cfg, "head")

        yield {"url": async_url}

@pytest.fixture(scope="session")
def _test_engine(postgres_container):
    engine = create_async_engine(postgres_container["url"])
    yield engine
    asyncio.run(engine.dispose())

@pytest.fixture(scope="session")
def _test_sessionmaker(_test_engine):
    return async_sessionmaker(_test_engine, expire_on_commit=False)

@pytest.fixture(scope="session")
def api_client(_test_sessionmaker):
    original_db_session = DBDependency.db_session
    DBDependency.db_session = lambda self: _test_sessionmaker()

    with TestClient(app) as client:
        yield client

    DBDependency.db_session = original_db_session

@pytest.fixture(scope="session")
def _sync_engine(postgres_container):
    sync_url = postgres_container["url"].replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def _sync_sessionmaker(_sync_engine):
    return sessionmaker(bind=_sync_engine)

def _register_and_login(client, nickname, password="StrongPassword123!"):
    reg_result = client.post("/api/v1/auth/reg", json={
        "nickname": nickname,
        "email": f"{nickname}@test.com",
        "password": password
    })
    assert reg_result.status_code == 201, f"Пользователь не смог зарегистрироваться: {reg_result.text}"
    login_result = client.post("/api/v1/auth/login", json={
        "nickname": nickname,
        "password": password
    })
    assert login_result.status_code == 200, f"Пользователь не смог войти в аккаунт: {login_result.text}"
    return client

@pytest.fixture
def student_client(api_client):
    nickname = f"student_{uuid.uuid4().hex[:6]}"
    return _register_and_login(api_client, nickname)

TEST_SECRET_LINK = "test_custom_link_123"

def _set_application_link(client, secret_part):
    result = client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_part})
    assert result.status_code == 200, f"Не удалось установить ссылку для заявки на преподавателя: {result.text}"
    return secret_part

@pytest.fixture
def professor_client(api_client, _sync_sessionmaker):
    admin_nickname = f"admin_{uuid.uuid4().hex[:6]}"
    admin_password = "StrongPassword123!"
    admin_reg_result = api_client.post("/api/v1/auth/reg", json={
        "email": f"{admin_nickname}@test.com",
        "nickname": admin_nickname,
        "password": admin_password
    })
    assert admin_reg_result.status_code == 201, f"Пользователь не смог зарегистрироваться: {admin_reg_result.text}"
    admin_login_result = api_client.post("/api/v1/auth/login", json={
        "nickname": admin_nickname,
        "password": admin_password
    })
    assert admin_login_result.status_code == 200, f"Пользователь не смог войти в аккаунт: {admin_login_result.text}"
    admin_profile = api_client.get("/api/v1/users/profile")
    assert admin_profile.status_code == 200, f"Не удалось получить данные пользователя: {admin_profile.text}"
    admin_id = admin_profile.json()["id"]
    with _sync_sessionmaker() as session:
        session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_id})
        session.commit()

    secret_link = _set_application_link(api_client, TEST_SECRET_LINK)

    admin_logout_result = api_client.get("/api/v1/auth/logout")
    assert admin_logout_result.status_code == 200, f"Администратор не смог выйти из аккаунта: {admin_logout_result.text}"
    api_client.cookies.clear()

    student_nickname = f"student_{uuid.uuid4().hex[:6]}"
    student_password = "StrongPassword123!"
    student_reg_result = api_client.post("/api/v1/auth/reg", json={
        "email": f"{student_nickname}@test.com",
        "nickname": student_nickname,
        "password": student_password
    })
    assert student_reg_result.status_code == 201, f"Пользователь не смог зарегистрироваться: {student_reg_result.text}"
    student_login_result = api_client.post("/api/v1/auth/login", json={
        "nickname": student_nickname,
        "password": student_password
    })
    assert student_login_result.status_code == 200, f"Пользователь не смог войти в аккаунт: {student_login_result.text}"
    student_profile = api_client.get("/api/v1/users/profile")
    assert student_profile.status_code == 200, f"Не удалось получить данные пользователя: {student_profile.text}"
    student_id = student_profile.json()["id"]

    submit_result = api_client.post(f"/api/v1/users/submit-professor-application/{secret_link}", json={
        "name": "Александр", "surname": "Евлампьев", "patronymic": "Александрович"
    })
    assert submit_result.status_code == 201, f"Не удалось подать заявку на преподавателя: {submit_result.text}"
    app_id = submit_result.json()["id"]

    student_logout_result = api_client.get("/api/v1/auth/logout")
    assert student_logout_result.status_code == 200, f"Студент не смог выйти из аккаунта: {student_logout_result.text}"
    api_client.cookies.clear()

    admin_login_result = api_client.post("/api/v1/auth/login", json={
        "nickname": admin_nickname,
        "password": admin_password
    })
    assert admin_login_result.status_code == 200, f"Администратор не смог войти в аккаунт: {admin_login_result.text}"

    approve_result = api_client.put("/api/v1/users/change-application-status", json={
        "application_id": app_id,
        "user_id": student_id,
        "status": "approved"
    })
    assert approve_result.status_code == 204, f"Не удалось одобрить заявку на преподавателя: {approve_result.text}"

    admin_logout_result = api_client.get("/api/v1/auth/logout")
    assert admin_logout_result.status_code == 200, f"Администратор не смог выйти из аккаунта: {admin_logout_result.text}"
    api_client.cookies.clear()

    professor_auth_result = api_client.post("/api/v1/auth/login", json={
        "nickname": student_nickname,
        "password": student_password
    })
    assert professor_auth_result.status_code == 200, f"Студент не смог войти в аккаунт: {professor_auth_result.text}"

    return api_client

@pytest.fixture
def admin_client(api_client, _sync_sessionmaker):
    nickname = f"admin_{uuid.uuid4().hex[:6]}"
    password = "StrongPassword123!"
    reg_result = api_client.post("/api/v1/auth/reg", json={
        "nickname": nickname,
        "email": f"{nickname}@test.com",
        "password": password
    })
    assert reg_result.status_code == 201, f"Пользователь не смог зарегистрироваться: {reg_result.text}"
    login_result = api_client.post("/api/v1/auth/login", json={
        "nickname": nickname,
        "password": password
    })
    assert login_result.status_code == 200, f"Пользователь не смог войти в аккаунт: {login_result.text}"
    profile = api_client.get("/api/v1/users/profile")
    assert profile.status_code == 200, f"Не удалось получить данные пользователя: {profile.text}"
    user_id = profile.json()["id"]

    with _sync_sessionmaker() as session:
        session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": user_id})
        session.commit()

    api_client.cookies.clear()
    login_result = api_client.post("/api/v1/auth/login", json={
        "nickname": nickname,
        "password": password
    })
    assert login_result.status_code == 200, f"Администратор не смог войти в аккаунт: {login_result.text}"
    return api_client