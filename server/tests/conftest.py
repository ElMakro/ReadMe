import os
import socket
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
import pytest_asyncio
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

TEST_DB_USER = os.environ.get("DB_USER", "test")
TEST_DB_PASSWORD = os.environ.get("DB_PASSWORD", "test")
TEST_DB_NAME = os.environ.get("DB_NAME", "test")
TEST_DB_HOST = os.environ.get("DB_HOST", "localhost")
TEST_DB_PORT = int(os.environ.get("DB_PORT", "5434"))

TEST_REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
TEST_REDIS_PORT = int(os.environ.get("REDIS_PORT", "6380"))
TEST_REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "test")
TEST_REDIS_DB = 0

TEST_DB_URL = f"postgresql+asyncpg://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
TEST_REDIS_URL = f"redis://:{TEST_REDIS_PASSWORD}@{TEST_REDIS_HOST}:{TEST_REDIS_PORT}/{TEST_REDIS_DB}"

os.environ["SECRET_KEY"] = "a" * 32


def _is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def docker_compose_file() -> str:
    return "docker-compose.test.yml"


@pytest.fixture(scope="session")
def postgres_service(docker_services):
    docker_services.wait_until_responsive(
        check=lambda: _is_port_open(TEST_DB_HOST, TEST_DB_PORT),
        timeout=60.0,
        pause=1.0,
    )
    return TEST_DB_URL


@pytest.fixture(scope="session")
def redis_service(docker_services):
    docker_services.wait_until_responsive(
        check=lambda: _is_port_open(TEST_REDIS_HOST, TEST_REDIS_PORT),
        timeout=60.0,
        pause=1.0,
    )
    return TEST_REDIS_URL


@pytest_asyncio.fixture(scope="function")
async def db_engine(postgres_service) -> AsyncGenerator[AsyncEngine]:
    from server.database.models.base import Base

    engine = create_async_engine(TEST_DB_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def professor_factory(db_engine: AsyncEngine):
    from server.database.models import ProfessorsDetails, Users
    from server.enums.role import Role

    async_session = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _create(name="Иван", surname="Петров", patronymic="Сергеевич", nickname=None, email=None):
        async with async_session() as session, session.begin():
            user_id = uuid4()
            if nickname is None:
                nickname = f"prof_{user_id.hex[:8]}"
            if email is None:
                email = f"{nickname}@example.com"

            user = Users(
                id=user_id,
                nickname=nickname,
                email=email,
                password="test_password",
                role=Role.PROFESSOR
            )
            session.add(user)

            professor = ProfessorsDetails(
                id=user_id,
                name=name,
                surname=surname,
                patronymic=patronymic
            )
            session.add(professor)
            await session.flush()
            await session.refresh(professor)
            return professor

    return _create


@pytest_asyncio.fixture(scope="function")
async def student_factory(db_engine: AsyncEngine):
    from server.database.models import Users
    from server.enums.role import Role

    async_session = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _create(nickname=None, email=None):
        async with async_session() as session, session.begin():
            user_id = uuid4()
            if nickname is None:
                nickname = f"student_{user_id.hex[:8]}"
            if email is None:
                email = f"{nickname}@example.com"

            user = Users(
                id=user_id,
                nickname=nickname,
                email=email,
                password="test_password",
                role=Role.STUDENT
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user

    return _create


@pytest_asyncio.fixture(scope="function")
async def course_factory(db_engine: AsyncEngine, professor_factory):
    from server.database.models import Courses

    async_session = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _create(
            name="Тестовый курс",
            description="Описание тестового курса",
            professor_id=None,
            is_public=True,
            is_content_public=True,
            tags=None
    ):
        async with async_session() as session, session.begin():
            if professor_id is None:
                professor = await professor_factory()
                professor_id = professor.id

            course = Courses(
                name=name,
                description=description,
                professor_id=professor_id,
                is_public=is_public,
                is_content_public=is_content_public,
                tags=tags or []
            )
            session.add(course)
            await session.flush()
            await session.refresh(course)
            return course

    return _create


@pytest_asyncio.fixture(scope="function")
async def enrollment_factory(db_engine: AsyncEngine, student_factory, course_factory):
    from server.database.models import CoursesForStudents

    async_session = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _create(student_id=None, course_id=None):
        async with async_session() as session, session.begin():
            if student_id is None:
                student = await student_factory()
                student_id = student.id
            if course_id is None:
                course = await course_factory()
                course_id = course.id

            enrollment = CoursesForStudents(
                student_id=student_id,
                course_id=course_id
            )
            session.add(enrollment)
            await session.flush()
            await session.refresh(enrollment)
            return enrollment

    return _create


class MockCoursesResourcesManager:
    def create_course_directory(self, course_id):
        pass

    def delete_course_directory(self, course_id):
        pass

    def create_section_directory(self, section_id, course_id):
        pass

    def delete_section_directory(self, section_id, course_id):
        pass

    def create_topic_directory(self, topic_directory_path):
        pass

    def delete_topic_directory(self, topic_directory_path):
        pass

    async def set_course_icon(self, course_id, icon_upload_file):
        pass

    def get_course_icon_path(self, course_id):
        return "/fake/path"

    async def upload_topic_resource(self, topic_directory_path, server_filename, resource):
        pass

    async def get_topic_resource(self, topic_directory_path, resource_filename):
        return "/fake/path"

    async def render_topic(self, topic_directory_path, raw_content):
        return raw_content


@pytest.fixture(scope="function")
def db_dependency(db_engine: AsyncEngine):
    class MockDBDependency:
        def __init__(self, engine):
            self._engine = engine
            self._session_factory = async_sessionmaker(
                bind=engine,
                expire_on_commit=False,
                autocommit=False,
            )

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def db_session(self):
            return self._session_factory()

    return MockDBDependency(db_engine)

@pytest.fixture(scope="function")
def redis_dependency(redis_service):
    class MockRedisDependency:
        def __init__(self):
            self._url = TEST_REDIS_URL
            self._pool = ConnectionPool.from_url(TEST_REDIS_URL, encoding="utf-8", decode_responses=True)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        @asynccontextmanager
        async def get_client(self):
            redis_client = Redis(connection_pool=self._pool)
            try:
                yield redis_client
            finally:
                await redis_client.aclose()

    return MockRedisDependency()


@pytest_asyncio.fixture(scope="function")
async def redis_client(redis_dependency) -> AsyncGenerator[Redis]:
    async with redis_dependency.get_client() as client:
        yield client

@pytest.fixture(scope="function")
def courses_manager(db_dependency):
    from server.app.api.v1.courses.courses_manager import CoursesManager
    return CoursesManager(db=db_dependency)


@pytest.fixture(scope="function")
def users_manager(db_dependency):
    from server.app.api.v1.users.users_manager import UsersManager
    return UsersManager(db=db_dependency)


@pytest.fixture(scope="function")
def auth_manager(db_dependency, redis_dependency):
    from server.app.api.v1.auth.auth_manager import AuthManager
    return AuthManager(db=db_dependency, redis=redis_dependency)


@pytest.fixture(scope="function")
def users_service(users_manager, auth_manager, db_engine):
    from server.app.api.v1.courses.courses_manager import CoursesManager
    from server.app.api.v1.users.secret_application_link_handler import SecretApplicationLinkHandler
    from server.app.api.v1.users.users_service import UsersService
    from server.data.users_resources.users_resources_manager import UsersResourcesManager

    courses_manager = CoursesManager(db=users_manager.db)
    users_resources_manager = UsersResourcesManager()
    secret_link_handler = SecretApplicationLinkHandler()

    return UsersService(
        auth_manager=auth_manager,
        users_manager=users_manager,
        courses_manager=courses_manager,
        users_resources_manager=users_resources_manager,
        secret_link_handler=secret_link_handler,
    )


@pytest.fixture(scope="function")
def courses_resources_manager():
    return MockCoursesResourcesManager()


@pytest.fixture(scope="function")
def courses_service(
        courses_manager,
        users_manager,
        users_service,
        courses_resources_manager,
        auth_manager,
):
    from server.app.api.v1.courses.courses_service import CoursesService

    return CoursesService(
        courses_manager=courses_manager,
        auth_manager=auth_manager,
        users_manager=users_manager,
        users_service=users_service,
        courses_resources_manager=courses_resources_manager,
    )


@pytest_asyncio.fixture(scope="function")
async def setup_professor_and_course(professor_factory, course_factory):
    professor = await professor_factory()
    course = await course_factory(professor_id=professor.id)
    return professor, course


@pytest_asyncio.fixture(scope="function")
async def setup_student_and_course(student_factory, course_factory, enrollment_factory):
    student = await student_factory()
    course = await course_factory()
    enrollment = await enrollment_factory(student_id=student.id, course_id=course.id)
    return student, course, enrollment
