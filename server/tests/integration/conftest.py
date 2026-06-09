"""
Фикстуры для интеграционных тестов ReadMe.
• PostgreSQL в Docker через Testcontainers
• Ролевые клиенты: student, professor, admin (синхронные!)
• Изоляция через подмену зависимости БД
"""
import os
import sys
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from testcontainers.postgres import PostgresContainer
from alembic.config import Config
from alembic import command

# 🔧 ИСПРАВЛЕНИЕ 1: __file__ (с двойными подчеркиваниями) и ТРИ уровня вверх ('..', '..', '..')
# conftest.py лежит в server/tests/integration/, а alembic.ini в корне ReadMe
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from server.main import app
from server.config.db_dependency import DBDependency


@pytest.fixture(scope="session")
def postgres_container():
    """🐳 Поднимает PostgreSQL в Docker и применяет миграции Alembic"""
    print("🐳 Запускаем PostgreSQL в Docker...")
    with PostgresContainer("postgres:18") as postgres:
        # 1. Получаем URL от testcontainers (по умолчанию он синхронный: postgresql+psycopg2://...)
        sync_url = postgres.get_connection_url()
        print(f"✅ PostgreSQL запущен: {sync_url}")

        # 🔧 КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ:
        # Твой server/database/alembic/env.py использует async_engine_from_config,
        # поэтому Alembic ожидает URL с драйвером asyncpg, а не psycopg2.
        # Преобразуем URL в асинхронный ПЕРЕД передачей в Alembic.
        async_url = sync_url.replace("+psycopg2", "+asyncpg")

        print("🔧 Применяем миграции Alembic...")

        # 2. Инициализируем конфигурацию Alembic, указывая путь к alembic.ini
        alembic_ini_path = os.path.join(project_root, "alembic.ini")
        alembic_cfg = Config(alembic_ini_path)

        # 3. Явно задаем script_location, чтобы Alembic точно нашел папку с миграциями
        script_location = os.path.join(project_root, "server", "database", "alembic")
        alembic_cfg.set_main_option("script_location", script_location)

        # 4. Переопределяем URL подключения на АСИНХРОННЫЙ URL из testcontainers
        alembic_cfg.set_main_option("sqlalchemy.url", async_url)

        # 5. Применяем все миграции до актуальной версии (head)
        # Alembic сам запустит asyncio.run() внутри env.py и накатит миграции
        command.upgrade(alembic_cfg, "head")
        print("✅ Миграции успешно применены (включая триггеры)")

        # 6. Возвращаем уже готовый async_url для использования в FastAPI
        yield {"url": async_url}

    print("🧹 PostgreSQL контейнер остановлен")


# ... далее идут твои остальные фикстуры (_test_engine, _test_sessionmaker, api_client и т.д.) БЕЗ ИЗМЕНЕНИЙ ...

# 🔧 ФИКСТУРЫ ДЛЯ АСИНХРОННОГО ПРИЛОЖЕНИЯ
@pytest.fixture(scope="session")
def _test_engine(postgres_container):
    """Внутренняя фикстура: асинхронный тестовый движок"""
    engine = create_async_engine(postgres_container["url"])
    yield engine
    import asyncio
    asyncio.run(engine.dispose())


@pytest.fixture(scope="session")
def _test_sessionmaker(_test_engine):
    """Внутренняя фикстура: фабрика асинхронных сессий"""
    return async_sessionmaker(_test_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def api_client(_test_sessionmaker):
    """🔧 Базовый клиент + подмена зависимости БД"""
    original_db_session = DBDependency.db_session
    DBDependency.db_session = lambda self: _test_sessionmaker()

    with TestClient(app) as client:
        yield client

    DBDependency.db_session = original_db_session


# 🔧 ФИКСТУРЫ ДЛЯ СИНХРОННЫХ ОПЕРАЦИЙ (смена ролей)
@pytest.fixture(scope="session")
def _sync_engine(postgres_container):
    """Внутренняя фикстура: синхронный движок для фикстур"""
    # 🔧 Используем psycopg2 для синхронных операций
    sync_url = postgres_container["url"].replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def _sync_sessionmaker(_sync_engine):
    """Внутренняя фикстура: фабрика синхронных сессий"""
    from sqlalchemy.orm import sessionmaker
    return sessionmaker(bind=_sync_engine)


# 🔧 ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ
def _register_and_login(client, nickname, password="StrongPassword123!"):
    """Регистрация + вход через API"""
    client.post("/api/v1/auth/reg", json={
        "nickname": nickname,
        "email": f"{nickname}@test.com",
        "password": password
    })
    client.post("/api/v1/auth/login", json={
        "nickname": nickname,
        "password": password
    })
    return client


# 🔧 РОЛЕВЫЕ ФИКСТУРЫ (ПОЛНОСТЬЮ СИНХРОННЫЕ!)
@pytest.fixture
def student_client(api_client):
    """🎓 Клиент с ролью student (по умолчанию при регистрации)"""
    nick = f"student_{uuid.uuid4().hex[:6]}"
    return _register_and_login(api_client, nick)


TEST_SECRET_LINK = "test_custom_link_123"

def _set_application_link(client, secret_part):
    """Установить кастомную ссылку (клиент должен быть админом)"""
    res = client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_part})
    assert res.status_code == 200, f"Failed to set application link: {res.text}"
    return secret_part

@pytest.fixture
def professor_client(api_client, _sync_sessionmaker):
    """Создаёт преподавателя через полный цикл с кастомной ссылкой."""
    # 1. Создаём админа
    admin_nick = f"admin_{uuid.uuid4().hex[:6]}"
    admin_password = "StrongPassword123!"
    api_client.post("/api/v1/auth/reg", json={
        "email": f"{admin_nick}@test.com",
        "nickname": admin_nick,
        "password": admin_password
    })
    api_client.post("/api/v1/auth/login", json={
        "nickname": admin_nick,
        "password": admin_password
    })
    admin_profile = api_client.get("/api/v1/users/profile").json()
    admin_id = admin_profile["id"]
    with _sync_sessionmaker() as session:
        session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_id})
        session.commit()

    # Устанавливаем кастомную ссылку
    secret_link = _set_application_link(api_client, TEST_SECRET_LINK)

    # Выходим из админа
    api_client.get("/api/v1/auth/logout")
    api_client.cookies.clear()

    # 2. Создаём студента
    student_nick = f"student_{uuid.uuid4().hex[:6]}"
    student_password = "StrongPassword123!"
    api_client.post("/api/v1/auth/reg", json={
        "email": f"{student_nick}@test.com",
        "nickname": student_nick,
        "password": student_password
    })
    api_client.post("/api/v1/auth/login", json={
        "nickname": student_nick,
        "password": student_password
    })
    student_profile = api_client.get("/api/v1/users/profile").json()
    student_id = student_profile["id"]

    # 3. Подаём заявку по кастомной ссылке
    submit_res = api_client.post(f"/api/v1/users/submit-professor-application/{secret_link}", json={
        "name": "Prof", "surname": "Test", "patronymic": "NeStudent"
    })
    assert submit_res.status_code == 201, f"Failed to submit application: {submit_res.text}"
    app_id = submit_res.json()["id"]

    # Выходим из студента
    api_client.get("/api/v1/auth/logout")
    api_client.cookies.clear()

    # 4. Админ заходит снова и одобряет заявку
    api_client.post("/api/v1/auth/login", json={
        "nickname": admin_nick,
        "password": admin_password
    })
    approve_res = api_client.put("/api/v1/users/change-application-status", json={
        "application_id": app_id,
        "user_id": student_id,
        "status": "approved"
    })
    assert approve_res.status_code in [200, 204], f"Approval failed: {approve_res.text}"

    # Обновляем роль в БД на всякий случай
    with _sync_sessionmaker() as session:
        session.execute(text("UPDATE users SET role = 'PROFESSOR' WHERE id = :uid"), {"uid": student_id})
        session.commit()

    # Выходим из админа
    api_client.get("/api/v1/auth/logout")
    api_client.cookies.clear()

    # 5. Студент (теперь профессор) заходит
    login_res = api_client.post("/api/v1/auth/login", json={
        "nickname": student_nick,
        "password": student_password
    })
    assert login_res.status_code == 200, f"Student login failed: {login_res.text}"

    return api_client


@pytest.fixture
def admin_client(api_client, _sync_sessionmaker):
    """🛡️ Клиент с ролью admin (создаётся с нуля)"""
    nick = f"admin_{uuid.uuid4().hex[:6]}"
    password = "StrongPassword123!"

    api_client.post("/api/v1/auth/reg", json={
        "nickname": nick,
        "email": f"{nick}@test.com",
        "password": password
    })
    api_client.post("/api/v1/auth/login", json={
        "nickname": nick,
        "password": password
    })
    profile = api_client.get("/api/v1/users/profile").json()
    user_id = profile["id"]

    with _sync_sessionmaker() as session:
        session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": user_id})
        session.commit()

    # Перелогиниваемся, чтобы токен обновился
    api_client.cookies.clear()
    login_res = api_client.post("/api/v1/auth/login", json={
        "nickname": nick,
        "password": password
    })
    assert login_res.status_code == 200
    return api_client