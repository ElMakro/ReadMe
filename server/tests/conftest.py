import os
import socket
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from server.app.api.v1.auth.auth_manager import AuthManager
from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.sections.sections_manager import SectionsManager
from server.app.api.v1.topics.topics import TopicContent, TopicContentBlock
from server.app.api.v1.topics.topics_manager import TopicsManager
from server.app.api.v1.users.users_manager import UsersManager
from server.database.models import Courses, CoursesForStudents, Sections, Topics

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
os.environ["SECRET_LINK_KEY"] = "jOlDKyBBqp8okb9sS-E6FzTXyTv0viu3aessVKSdLSU="
os.environ["DEFAULT_SECRET_APPLICATION_LINK_PART"] = "test"


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
async def section_factory(db_engine, course_factory):
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _create(
            course_id=None,
            name="Тестовый раздел",
            description="Описание тестового раздела",
            order_number=None,
            tags=None,
    ):
        async with async_session() as session, session.begin():
            if course_id is None:
                course = await course_factory()
                course_id = course.id

            if order_number is None:
                result = await session.execute(
                    select(func.max(Sections.order_number)).where(Sections.course_id == course_id)
                )
                max_order = result.scalar() or 0
                order_number = max_order + 1

            section = Sections(
                id=uuid4(),
                course_id=course_id,
                name=name,
                description=description,
                order_number=order_number,
                tags=tags or [],
            )
            session.add(section)
            await session.flush()
            await session.refresh(section)
            return section

    return _create


@pytest_asyncio.fixture(scope="function")
async def topic_factory(db_engine, section_factory):
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _create(
            section_id=None,
            name="Тестовая тема",
            order_number=None,
            course_id=None,
            tags=None,
            raw_content=None,
            topic_directory_path=None,
    ):
        async with async_session() as session, session.begin():
            if section_id is None:
                section = await section_factory()
                section_id = section.id
                course_id = section.course_id
            else:
                if course_id is None:
                    result = await session.execute(
                        select(Sections.course_id).where(Sections.id == section_id)
                    )
                    course_id = result.scalar_one()

            if order_number is None:
                result = await session.execute(
                    select(func.max(Topics.order_number)).where(Topics.section_id == section_id)
                )
                max_order = result.scalar() or 0
                order_number = max_order + 1

            if raw_content is None:
                raw_content = TopicContent(root=[
                    TopicContentBlock(type="markdown", content=["# Заголовок темы"])
                ])

            if topic_directory_path is None:
                topic_directory_path = Path(f"/tmp/test_topic_{uuid4().hex[:8]}")

            topic = Topics(
                id=uuid4(),
                section_id=section_id,
                name=name,
                order_number=order_number,
                course_id=course_id,  # <-- теперь course_id всегда будет задан
                tags=tags or [],
                raw_content=[block.model_dump() for block in raw_content.root],
                rendered_content=[block.model_dump() for block in raw_content.root],
                topic_directory_path=topic_directory_path,
            )
            session.add(topic)
            await session.flush()
            await session.refresh(topic)
            return topic

    return _create


@pytest_asyncio.fixture(scope="function")
async def enrollment_factory(db_engine: AsyncEngine, student_factory, course_factory):
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
    return CoursesManager(db=db_dependency)


@pytest.fixture(scope="function")
def users_manager(db_dependency):
    return UsersManager(db=db_dependency)


@pytest.fixture(scope="function")
def auth_manager(db_dependency, redis_dependency):
    return AuthManager(db=db_dependency, redis=redis_dependency)


@pytest.fixture(scope="function")
def sections_manager(db_dependency):
    return SectionsManager(db=db_dependency)


@pytest.fixture(scope="function")
def topics_manager(db_dependency):
    return TopicsManager(db=db_dependency)


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
