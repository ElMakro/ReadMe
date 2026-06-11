import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from server.app.api.v1.exceptions import ConflictError, OperationPermissionError
from server.app.api.v1.topics.topics import (
    FileItem,
    TopicContent,
    TopicContentBlock,
    TopicIDMixin,
    TopicResponse,
    TopicsFullListResponse,
)
from server.app.api.v1.topics.topics_service import TopicsService
from server.enums.access_permissions import AccessPermissions
from server.enums.role import Role

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_users_service(mocker: MockerFixture):
    service = mocker.AsyncMock()
    service.check_course_access = mocker.AsyncMock()
    return service


@pytest.fixture
def mock_courses_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.get_course_by_id = mocker.AsyncMock()
    return manager


@pytest.fixture
def mock_sections_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.get_section_by_id = mocker.AsyncMock()
    return manager


@pytest.fixture
def mock_topics_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.create_topic = mocker.AsyncMock()
    manager.get_topic_by_id = mocker.AsyncMock()
    manager.get_topics_by_section_id = mocker.AsyncMock()
    manager.get_topics_by_course_id = mocker.AsyncMock()
    manager.delete_topic = mocker.AsyncMock()
    manager.update_topic = mocker.AsyncMock()
    manager.check_section_have_topic_with_order_number = mocker.AsyncMock()
    manager.get_and_block_topic = mocker.AsyncMock()
    manager.change_topic_content_and_unblock = mocker.AsyncMock()
    return manager


@pytest.fixture
def mock_courses_resources_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.create_topic_directory = mocker.MagicMock()
    manager.delete_topic_directory = mocker.MagicMock()
    manager.render_topic = mocker.AsyncMock()
    manager.upload_topic_resource = mocker.AsyncMock()
    manager.get_topic_resource = mocker.AsyncMock()
    return manager


@pytest.fixture
def topics_service(
    mock_users_service,
    mock_courses_manager,
    mock_sections_manager,
    mock_topics_manager,
    mock_courses_resources_manager,
) -> TopicsService:
    return TopicsService(
        users_service=mock_users_service,
        courses_manager=mock_courses_manager,
        sections_manager=mock_sections_manager,
        topics_manager=mock_topics_manager,
        courses_resources_manager=mock_courses_resources_manager,
    )


def create_topic_response_mock(
    topic_id: uuid.UUID = None,
    section_id: uuid.UUID = None,
    course_id: uuid.UUID = None,
    name: str = "Test Topic",
    order_number: int = 1,
    tags: list[str] = None,
    topic_directory_path: Path = None,
) -> TopicResponse:
    from datetime import datetime

    return TopicResponse(
        id=topic_id or uuid.uuid4(),
        section_id=section_id or uuid.uuid4(),
        course_id=course_id or uuid.uuid4(),
        name=name,
        order_number=order_number,
        tags=tags or [],
        raw_content=TopicContent(root=[]),
        rendered_content=TopicContent(root=[]),
        topic_directory_path=topic_directory_path or Path("/tmp/topic"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestCreateTopic:
    async def test_creates_topic_successfully(
        self,
        topics_service: TopicsService,
        mock_sections_manager,
        mock_courses_manager,
        mock_users_service,
        mock_topics_manager,
        mock_courses_resources_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        section_id = uuid.uuid4()
        topic_id = uuid.uuid4()
        section = MagicMock(id=section_id, course_id=uuid.uuid4())
        course = MagicMock(id=section.course_id)
        raw_content = TopicContent(root=[
            TopicContentBlock(type="markdown", content=["# Hello"])
        ])
        rendered_content = TopicContent(root=[
            TopicContentBlock(type="markdown", content=["<h1>Hello</h1>"])
        ])

        mock_sections_manager.get_section_by_id.return_value = section
        mock_courses_manager.get_course_by_id.return_value = course
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS
        mock_topics_manager.check_section_have_topic_with_order_number.return_value = False
        mock_courses_resources_manager.render_topic.return_value = rendered_content
        mock_topics_manager.create_topic.return_value = TopicIDMixin(id=topic_id)

        result = await topics_service.create_topic(
            user=user,
            section_id=section_id,
            name="Новая тема",
            order_number=1,
            tags=["test"],
            raw_content=raw_content,
        )

        assert result.id == topic_id
        mock_sections_manager.get_section_by_id.assert_awaited_once_with(section_id)
        mock_courses_manager.get_course_by_id.assert_awaited_once_with(section.course_id)
        mock_topics_manager.create_topic.assert_awaited_once()

    async def test_raises_error_when_no_edit_access(
        self,
        topics_service: TopicsService,
        mock_sections_manager,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        section_id = uuid.uuid4()
        section = MagicMock(course_id=uuid.uuid4())

        mock_sections_manager.get_section_by_id.return_value = section
        mock_courses_manager.get_course_by_id.return_value = MagicMock()
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="У пользователя нет права на создание темы в данном курсе!"):
            await topics_service.create_topic(
                user=user,
                section_id=section_id,
                name="Тема",
                order_number=1,
                tags=[],
                raw_content=TopicContent(root=[]),
            )

    async def test_raises_error_when_order_number_already_exists(
        self,
        topics_service: TopicsService,
        mock_sections_manager,
        mock_courses_manager,
        mock_users_service,
        mock_topics_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        section_id = uuid.uuid4()
        section = MagicMock(course_id=uuid.uuid4())

        mock_sections_manager.get_section_by_id.return_value = section
        mock_courses_manager.get_course_by_id.return_value = MagicMock()
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS
        mock_topics_manager.check_section_have_topic_with_order_number.return_value = True

        with pytest.raises(ConflictError, match="Тема с таким порядковым номером уже существует в этом разделе!"):
            await topics_service.create_topic(
                user=user,
                section_id=section_id,
                name="Тема",
                order_number=1,
                tags=[],
                raw_content=TopicContent(root=[]),
            )


class TestGetTopicById:
    async def test_returns_topic_when_has_access(
        self,
        topics_service: TopicsService,
        mock_topics_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        topic_id = uuid.uuid4()
        expected_topic = create_topic_response_mock(topic_id=topic_id)

        mock_topics_manager.get_topic_by_id.return_value = expected_topic
        mock_users_service.check_course_access.return_value = AccessPermissions.CONTENT_ACCESS

        result = await topics_service.get_topic_by_id(user, topic_id)

        assert result.id == topic_id
        mock_topics_manager.get_topic_by_id.assert_awaited_once_with(topic_id)

    async def test_raises_error_when_no_content_access(
        self,
        topics_service: TopicsService,
        mock_topics_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        topic_id = uuid.uuid4()
        expected_topic = create_topic_response_mock(topic_id=topic_id)

        mock_topics_manager.get_topic_by_id.return_value = expected_topic
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="Пользователь не имеет доступа к данной теме!"):
            await topics_service.get_topic_by_id(user, topic_id)


class TestGetTopicsBySectionId:
    async def test_returns_topics_when_has_access(
        self,
        topics_service: TopicsService,
        mock_sections_manager,
        mock_topics_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        section_id = uuid.uuid4()
        section = MagicMock(course_id=uuid.uuid4())
        expected_response = TopicsFullListResponse(root=[])

        mock_sections_manager.get_section_by_id.return_value = section
        mock_users_service.check_course_access.return_value = AccessPermissions.CONTENT_ACCESS
        mock_topics_manager.get_topics_by_section_id.return_value = expected_response

        result = await topics_service.get_topics_by_section_id(user, section_id)

        assert result == expected_response


class TestGetTopicsByCourseId:
    async def test_returns_topics_when_has_access(
        self,
        topics_service: TopicsService,
        mock_courses_manager,
        mock_topics_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        course_id = uuid.uuid4()
        course = MagicMock()
        expected_response = TopicsFullListResponse(root=[])

        mock_courses_manager.get_course_by_id.return_value = course
        mock_users_service.check_course_access.return_value = AccessPermissions.CONTENT_ACCESS
        mock_topics_manager.get_topics_by_course_id.return_value = expected_response

        result = await topics_service.get_topics_by_course_id(user, course_id)

        assert result == expected_response


class TestDeleteTopic:
    async def test_deletes_topic_successfully(
        self,
        topics_service: TopicsService,
        mock_topics_manager,
        mock_users_service,
        mock_courses_resources_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        topic_id = uuid.uuid4()
        topic = create_topic_response_mock(topic_id=topic_id)

        mock_topics_manager.get_topic_by_id.return_value = topic
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS

        await topics_service.delete_topic(user, topic_id)

        mock_topics_manager.delete_topic.assert_awaited_once_with(topic_id)
        mock_courses_resources_manager.delete_topic_directory.assert_called_once_with(
            topic.topic_directory_path
        )


class TestUpdateTopic:
    async def test_updates_topic_successfully(
        self,
        topics_service: TopicsService,
        mock_topics_manager,
        mock_users_service,
        mock_courses_resources_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        topic_id = uuid.uuid4()
        topic = create_topic_response_mock(
            topic_id=topic_id,
            name="Старое название",
            tags=["old"],
        )
        new_raw_content = TopicContent(root=[
            TopicContentBlock(type="markdown", content=["# Новый контент"])
        ])
        rendered_content = TopicContent(root=[
            TopicContentBlock(type="markdown", content=["<h1>Новый контент</h1>"])
        ])

        mock_topics_manager.get_topic_by_id.return_value = topic
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS
        mock_courses_resources_manager.render_topic.return_value = rendered_content

        await topics_service.update_topic(
            user=user,
            topic_id=topic_id,
            new_name="Новое название",
            new_tags=["new"],
            new_raw_content=new_raw_content,
        )

        mock_topics_manager.update_topic.assert_awaited_once_with(
            topic_id, "Новое название", ["new"], new_raw_content, rendered_content
        )


class TestUploadResource:
    async def test_upload_resource_successfully(
        self,
        topics_service: TopicsService,
        mock_topics_manager,
        mock_users_service,
        mock_courses_resources_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        topic_id = uuid.uuid4()
        block_number = 1
        file_number = 1
        resource = MagicMock()
        resource.filename = "test.txt"
        resource.read = AsyncMock(return_value=b"test content")

        topic_mock = MagicMock()
        topic_response = create_topic_response_mock(topic_id=topic_id)
        topic_response.raw_content = TopicContent(root=[
            TopicContentBlock(type="files", content=[
                FileItem(original_filename="test.txt", server_filename=None)
            ])
        ])

        session_mock = AsyncMock()

        mock_topics_manager.get_and_block_topic.return_value = (topic_mock, topic_response, session_mock)
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS

        result = await topics_service.upload_resource(
            user, topic_id, block_number, file_number, resource
        )

        assert result.original_filename == "test.txt"
        assert result.server_filename is not None
        mock_courses_resources_manager.upload_topic_resource.assert_awaited_once()
        mock_topics_manager.change_topic_content_and_unblock.assert_awaited_once()


class TestGetResource:
    async def test_returns_resource_path(
        self,
        topics_service: TopicsService,
        mock_topics_manager,
        mock_users_service,
        mock_courses_resources_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        topic_id = uuid.uuid4()
        resource_filename = "file.txt"
        expected_path = Path("/tmp/file.txt")

        topic = create_topic_response_mock(topic_id=topic_id)
        mock_topics_manager.get_topic_by_id.return_value = topic
        mock_users_service.check_course_access.return_value = AccessPermissions.HEADER_ACCESS
        mock_courses_resources_manager.get_topic_resource.return_value = expected_path

        result = await topics_service.get_resource(user, topic_id, resource_filename)

        assert result == expected_path
