# # # server/tests/integration/conftest.py
# # """
# # Фикстуры с Testcontainers:
# # • PostgreSQL поднимается в Docker автоматически
# # • Миграции применяются
# # • Контейнер удаляется после тестов
# # """
# # import os
# # import sys
# # import pytest
# # from testcontainers.postgres import PostgresContainer
# #
# # # Добавляем корень проекта в путь
# # project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# # if project_root not in sys.path:
# #     sys.path.insert(0, project_root)
# #
# # from fastapi.testclient import TestClient
# # from alembic.config import Config
# # from alembic import command
# #
# #
# # @pytest.fixture(scope="session")
# # def postgres_container():
# #     """
# #     Поднимает PostgreSQL в Docker на время тестов.
# #     Автоматически удаляется после завершения.
# #     """
# #     print("🐳 Запускаем PostgreSQL в Docker...")
# #
# #     # Создаём контейнер (образ postgres:15)
# #     with PostgresContainer("postgres:18") as postgres:
# #         # Получаем connection string
# #         connection_url = postgres.get_connection_url()
# #         print(f"✅ PostgreSQL запущен: {connection_url}")
# #
# #         # Применяем миграции
# #         print("🔧 Применяем миграции...")
# #         alembic_cfg = Config(os.path.join(project_root, "..", "alembic.ini"))
# #         # 🔧 Указываем абсолютный путь к миграциям
# #         alembic_cfg.set_main_option(
# #             "script_location",
# #             os.path.join(project_root, "database", "alembic")
# #         )
# #         alembic_cfg.set_main_option("sqlalchemy.url", connection_url)
# #         command.upgrade(alembic_cfg, "head")
# #         print("✅ Миграции применены")
# #
# #         # Извлекаем параметры для переменных окружения
# #         # connection_url выглядит как: postgresql+psycopg2://user:pass@host:port/db
# #         yield {
# #             "url": connection_url,
# #             "host": postgres.get_container_host_ip(),
# #             "port": postgres.get_exposed_port(5432),
# #             "user": postgres.username,
# #             "password": postgres.password,
# #             "dbname": postgres.dbname
# #         }
# #
# #     print("🧹 PostgreSQL контейнер остановлен")
# #
# #
# # @pytest.fixture(scope="session")
# # def api_client(postgres_container):
# #     """
# #     Создаёт TestClient с подключением к тестовой БД из контейнера.
# #     """
# #     # Переопределяем переменные окружения для подключения к контейнеру
# #     os.environ["DB_HOST"] = postgres_container["host"]
# #     os.environ["DB_PORT"] = str(postgres_container["port"])
# #     os.environ["DB_USER"] = postgres_container["user"]
# #     os.environ["DB_PASSWORD"] = postgres_container["password"]
# #     os.environ["DB_NAME"] = postgres_container["dbname"]
# #
# #     # Перезагружаем приложение, чтобы оно подхватило новые настройки
# #     # (если нужно — можно использовать dependency_overrides)
# #     from server.main import app
# #
# #     with TestClient(app) as client:
# #         yield client
#
# """
# Фикстуры с Testcontainers для FastAPI.
# Минимальные изменения: подмена зависимости БД вместо os.environ.
# """
# import os
# import sys
# import pytest
# import asyncio
# from testcontainers.postgres import PostgresContainer
# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
#
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)
#
# from fastapi.testclient import TestClient
# from server.main import app
#
# # 🔧 Импортируйте вашу базовую модель (адаптируйте путь!)
# from server.database.models.base import Base  # ← Проверьте этот путь!
#
#
# @pytest.fixture(scope="session")
# def postgres_container():
#     """Поднимает PostgreSQL в Docker и создаёт схему"""
#     print("🐳 Запускаем PostgreSQL в Docker...")
#
#     with PostgresContainer("postgres:18") as postgres:
#         connection_url = postgres.get_connection_url().replace("+psycopg2", "+asyncpg")
#         print(f"✅ PostgreSQL запущен: {connection_url}")
#
#         # 🔧 Создаём таблицы напрямую из моделей (проще и надёжнее, чем Alembic)
#         print("🔧 Создаём схему из моделей...")
#
#         async def create_tables():
#             engine = create_async_engine(connection_url)
#             async with engine.begin() as conn:
#                 await conn.run_sync(Base.metadata.create_all)
#             await engine.dispose()
#
#         asyncio.run(create_tables())
#         print("✅ Схема создана")
#
#         yield {"url": connection_url}
#
#     print("🧹 PostgreSQL контейнер остановлен")
#
#
# @pytest.fixture(scope="session")
# def api_client(postgres_container):
#     """Создаёт TestClient с подменой БД на тестовую"""
#
#     # 🔧 Создаём тестовый движок из URL контейнера
#     test_engine = create_async_engine(postgres_container["url"])
#     test_sessionmaker = async_sessionmaker(test_engine, expire_on_commit=False)
#
#     # 🔧 Подменяем зависимость БД
#     from server.config.db_dependency import DBDependency
#
#     # Сохраняем оригинал для восстановления
#     original_db_session = DBDependency.db_session
#
#     # 🔧 КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ:
#     # Возвращаем сам sessionmaker, а не генератор!
#     # Потому что приложение делает: async with self.db.db_session() as session
#     # А sessionmaker() уже возвращает async context manager
#     DBDependency.db_session = lambda self: test_sessionmaker()
#
#     # Создаём клиент
#     with TestClient(app) as client:
#         yield client
#
#     # 🔧 Восстанавливаем оригинал
#     DBDependency.db_session = original_db_session
#
#     # Закрываем движок
#     import asyncio
#     asyncio.run(test_engine.dispose())
# server/tests/integration/conftest.py
"""
Фикстуры для интеграционных тестов ReadMe.
• PostgreSQL в Docker через Testcontainers
• Ролевые клиенты: student, professor, admin (синхронные!)
• Изоляция через подмену зависимости БД
"""
import os
import sys
import pytest
import uuid
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import create_engine, text  # ← Синхронные импорты

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from server.main import app
from server.database.models.base import Base
from server.config.db_dependency import DBDependency


@pytest.fixture(scope="session")
def postgres_container():
    """🐳 Поднимает PostgreSQL в Docker и создаёт схему"""
    print("🐳 Запускаем PostgreSQL в Docker...")
    with PostgresContainer("postgres:18") as postgres:
        # Заменяем синхронный драйвер на асинхронный asyncpg для основного приложения
        connection_url = postgres.get_connection_url().replace("+psycopg2", "+asyncpg")
        print(f"✅ PostgreSQL запущен: {connection_url}")

        print("🔧 Создаём схему из моделей...")

        async def create_tables():
            engine = create_async_engine(connection_url)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await engine.dispose()

        import asyncio
        asyncio.run(create_tables())
        print("✅ Схема создана")
        yield {"url": connection_url}
    print("🧹 PostgreSQL контейнер остановлен")


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


@pytest.fixture
def professor_client(admin_client, student_client, _sync_sessionmaker):
    """
    Создаём реального преподавателя через заявку и одобрение.
    """
    # 1. Подаём заявку от студента
    submit_res = student_client.post("/api/v1/users/submit-professor-application", json={
        "name": "Prof", "surname": "Test"
    })
    app_id = submit_res.json()["id"]
    student_profile = student_client.get("/api/v1/users/profile").json()
    student_id = student_profile["id"]

    # 2. Админ одобряет
    admin_client.put("/api/v1/users/change-application-status", json={
        "application_id": app_id,
        "user_id": student_id,
        "status": "approved"
    })

    # 3. Явно обновляем роль в БД до 'PROFESSOR' (на случай, если эндпоинт не меняет роль)
    with _sync_sessionmaker() as session:
        session.execute(
            text("UPDATE users SET role = 'PROFESSOR' WHERE id = :uid"),
            {"uid": student_id}
        )
        session.commit()

    # 4. Очищаем cookies и перелогиниваемся (используем тот же student_client!)
    student_client.cookies.clear()
    student_client.post("/api/v1/auth/login", json={
        "nickname": student_profile["nickname"],
        "password": "StrongPassword123!"
    })

    return student_client


@pytest.fixture
def admin_client(api_client, _sync_sessionmaker):
    """🛡️ Клиент с ролью admin"""
    nick = f"admin_{uuid.uuid4().hex[:6]}"
    password = "StrongPassword123!"

    # 1. Регистрация и логин
    client = _register_and_login(api_client, nick, password)

    # 2. Получаем ID пользователя
    profile = client.get("/api/v1/users/profile").json()
    user_id = profile["id"]
    print(f"🔧 Создаём админа: {nick}, ID: {user_id}")

    # 3. Обновляем роль в БД
    with _sync_sessionmaker() as session:
        result = session.execute(
            text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"),
            {"uid": user_id}
        )
        session.commit()
        print(f"🔧 Обновлено строк: {result.rowcount}")

        # Проверяем, что роль действительно изменилась
        check = session.execute(
            text("SELECT role FROM users WHERE id = :uid"),
            {"uid": user_id}
        ).scalar()
        print(f"🔧 Роль в БД после UPDATE: {check}")

    # 4. Перелогиниваемся для обновления токена
    client.cookies.clear()
    login_res = client.post("/api/v1/auth/login", json={
        "nickname": nick,
        "password": password
    })
    print(f"🔧 Логин статус: {login_res.status_code}")

    # Проверяем профиль после логина
    new_profile = client.get("/api/v1/users/profile").json()
    print(f"🔧 Роль в профиле после логина: {new_profile.get('role')}")

    return client