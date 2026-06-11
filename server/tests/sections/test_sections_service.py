import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from server.app.api.v1.exceptions import ConflictError, ObjectMissingError, OperationPermissionError
from server.app.api.v1.sections.sections import SectionIDMixin, SectionResponse, SectionsFullListResponse
from server.app.api.v1.sections.sections_manager import DifferentSourcesContentSwapError
from server.app.api.v1.sections.sections_service import SectionsService
from server.enums.access_permissions import AccessPermissions
from server.enums.role import Role

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_courses_resources_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.create_section_directory = mocker.AsyncMock()
    manager.delete_section_directory = mocker.AsyncMock()
    return manager


@pytest.fixture
def mock_sections_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.create_section = mocker.AsyncMock()
    manager.get_section_by_id = mocker.AsyncMock()
    manager.get_topics_by_course_id = mocker.AsyncMock()
    manager.delete_section = mocker.AsyncMock()
    manager.update_section = mocker.AsyncMock()
    manager.swap_sections = mocker.AsyncMock()
    manager.check_course_have_section_with_order_number = mocker.AsyncMock()
    return manager


@pytest.fixture
def mock_courses_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.get_course_by_id = mocker.AsyncMock()
    return manager


@pytest.fixture
def mock_users_service(mocker: MockerFixture):
    service = mocker.AsyncMock()
    service.check_course_access = mocker.AsyncMock()
    return service


@pytest.fixture
def sections_service(
    mock_courses_resources_manager,
    mock_sections_manager,
    mock_courses_manager,
    mock_users_service,
) -> SectionsService:
    return SectionsService(
        courses_resources_service=mock_courses_resources_manager,
        sections_manager=mock_sections_manager,
        courses_manager=mock_courses_manager,
        users_service=mock_users_service,
        data_manager=mock_courses_resources_manager,
    )


def create_section_response_mock(
    section_id: uuid.UUID = None,
    course_id: uuid.UUID = None,
    name: str = "Test Section",
    description: str = "Description",
    order_number: int = 1,
    tags: list[str] = None,
) -> SectionResponse:
    return SectionResponse(
        id=section_id or uuid.uuid4(),
        course_id=course_id or uuid.uuid4(),
        name=name,
        description=description,
        order_number=order_number,
        tags=tags or [],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestCreateSection:
    async def test_creates_section_successfully(
        self,
        sections_service: SectionsService,
        mock_courses_manager,
        mock_sections_manager,
        mock_users_service,
        mock_courses_resources_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        section_id = uuid.uuid4()

        mock_courses_manager.get_course_by_id.return_value = MagicMock()
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS
        mock_sections_manager.check_course_have_section_with_order_number.return_value = False
        mock_sections_manager.create_section.return_value = SectionIDMixin(id=section_id)

        result = await sections_service.create_section(
            user=user,
            course_id=course_id,
            name="Новый раздел",
            description="Описание",
            order_number=1,
            tags=["test"],
        )

        assert result.id == section_id
        mock_courses_manager.get_course_by_id.assert_awaited_once_with(course_id)
        mock_users_service.check_course_access.assert_awaited_once()
        mock_sections_manager.check_course_have_section_with_order_number.assert_awaited_once_with(course_id, 1)
        mock_sections_manager.create_section.assert_awaited_once_with(
            course_id, "Новый раздел", "Описание", 1, ["test"]
        )
        mock_courses_resources_manager.create_section_directory.assert_awaited_once_with(section_id, course_id)

    async def test_raises_error_when_no_edit_access(
        self,
        sections_service: SectionsService,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        course_id = uuid.uuid4()

        mock_courses_manager.get_course_by_id.return_value = MagicMock()
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="У пользователя, не являющегося владельцем курса или "
                                                           "администратором, нет права создавать темы в курсе!"):
            await sections_service.create_section(
                user=user,
                course_id=course_id,
                name="Раздел",
                description="",
                order_number=1,
                tags=[],
            )

    async def test_raises_error_when_order_number_already_exists(
        self,
        sections_service: SectionsService,
        mock_courses_manager,
        mock_sections_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()

        mock_courses_manager.get_course_by_id.return_value = MagicMock()
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS
        mock_sections_manager.check_course_have_section_with_order_number.return_value = True

        with pytest.raises(ConflictError, match="Раздел с таким порядковым номером уже существует!"):
            await sections_service.create_section(
                user=user,
                course_id=course_id,
                name="Раздел",
                description="",
                order_number=1,
                tags=[],
            )

    async def test_raises_error_when_course_not_found(
        self,
        sections_service: SectionsService,
        mock_courses_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()

        mock_courses_manager.get_course_by_id.side_effect = ObjectMissingError("Курса с таким ID не существует!")

        with pytest.raises(ObjectMissingError, match="Курса с таким ID не существует!"):
            await sections_service.create_section(
                user=user,
                course_id=course_id,
                name="Раздел",
                description="",
                order_number=1,
                tags=[],
            )


class TestGetSectionById:
    async def test_returns_section_when_has_access(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        section_id = uuid.uuid4()
        expected_section = create_section_response_mock(section_id=section_id)

        mock_sections_manager.get_section_by_id.return_value = expected_section
        mock_users_service.check_course_access.return_value = AccessPermissions.CONTENT_ACCESS

        result = await sections_service.get_section_by_id(user, section_id)

        assert result.id == section_id
        mock_sections_manager.get_section_by_id.assert_awaited_once_with(section_id)
        mock_users_service.check_course_access.assert_awaited_once_with(
            user, course_id=expected_section.course_id
        )

    async def test_raises_error_when_no_content_access(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        section_id = uuid.uuid4()
        expected_section = create_section_response_mock(section_id=section_id)

        mock_sections_manager.get_section_by_id.return_value = expected_section
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="Пользователь не имеет доступа к данному разделу!"):
            await sections_service.get_section_by_id(user, section_id)

    async def test_raises_error_when_section_not_found(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        section_id = uuid.uuid4()

        mock_sections_manager.get_section_by_id.side_effect = ObjectMissingError("Раздела курса с таким "
                                                                                 "идентификатором не существует!")

        with pytest.raises(ObjectMissingError, match="Раздела курса с таким идентификатором не существует!"):
            await sections_service.get_section_by_id(user, section_id)


class TestGetSectionsByCourseId:
    async def test_returns_sections_when_has_access(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        course_id = uuid.uuid4()
        expected_response = SectionsFullListResponse(root=[])

        mock_users_service.check_course_access.return_value = AccessPermissions.CONTENT_ACCESS
        mock_sections_manager.get_sections_by_course_id.return_value = expected_response

        result = await sections_service.get_sections_by_course_id(user, course_id)

        assert result == expected_response
        mock_users_service.check_course_access.assert_awaited_once_with(user, course_id=course_id)
        mock_sections_manager.get_sections_by_course_id.assert_awaited_once_with(course_id)

    async def test_raises_error_when_no_content_access(
        self,
        sections_service: SectionsService,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        course_id = uuid.uuid4()

        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="Пользователь не имеет прав "
                                                           "доступа к разделам данного курса"):
            await sections_service.get_sections_by_course_id(user, course_id)

    async def test_raises_error_when_course_not_found(
        self,
        sections_service: SectionsService,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()

        mock_users_service.check_course_access.side_effect = ObjectMissingError("Курса с таким ID не существует!")

        with pytest.raises(ObjectMissingError, match="Курса с таким ID не существует!"):
            await sections_service.get_sections_by_course_id(user, course_id)


class TestDeleteSection:
    async def test_deletes_section_successfully(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
        mock_users_service,
        mock_courses_resources_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        section_id = uuid.uuid4()
        section = create_section_response_mock(section_id=section_id, course_id=uuid.uuid4())

        mock_sections_manager.get_section_by_id.return_value = section
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS

        await sections_service.delete_section(user, section_id)

        mock_sections_manager.delete_section.assert_awaited_once_with(section_id)
        mock_courses_resources_manager.delete_section_directory.assert_awaited_once_with(
            section.id, section.course_id
        )

    async def test_raises_error_when_no_edit_access(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        section_id = uuid.uuid4()
        section = create_section_response_mock(section_id=section_id)

        mock_sections_manager.get_section_by_id.return_value = section
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="У пользователя нет прав на удаление данного раздела!"):
            await sections_service.delete_section(user, section_id)


class TestUpdateSection:
    async def test_updates_section_successfully(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        section_id = uuid.uuid4()
        section = create_section_response_mock(
            section_id=section_id,
            name="Старое название",
            description="Старое описание",
            tags=["old"],
        )

        mock_sections_manager.get_section_by_id.return_value = section
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS

        await sections_service.update_section(
            user=user,
            section_id=section_id,
            new_name="Новое название",
            new_description="Новое описание",
            new_tags=["new"],
        )

        mock_sections_manager.update_section.assert_awaited_once_with(
            section_id, "Новое название", "Новое описание", ["new"]
        )

    async def test_updates_only_specified_fields(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        section_id = uuid.uuid4()
        section = create_section_response_mock(
            section_id=section_id,
            name="Старое имя",
            description="Старое описание",
            tags=["old"],
        )

        mock_sections_manager.get_section_by_id.return_value = section
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS

        await sections_service.update_section(
            user=user,
            section_id=section_id,
            new_name="Новое имя",
            new_description=None,
            new_tags=None,
        )

        mock_sections_manager.update_section.assert_awaited_once_with(
            section_id, "Новое имя", "Старое описание", ["old"]
        )

    async def test_no_changes_when_all_none(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        section_id = uuid.uuid4()
        section = create_section_response_mock(section_id=section_id)

        mock_sections_manager.get_section_by_id.return_value = section
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS

        await sections_service.update_section(
            user=user,
            section_id=section_id,
            new_name=None,
            new_description=None,
            new_tags=None,
        )

        mock_sections_manager.update_section.assert_not_awaited()

    async def test_raises_error_when_no_edit_access(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        section_id = uuid.uuid4()
        section = create_section_response_mock(section_id=section_id)

        mock_sections_manager.get_section_by_id.return_value = section
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="У пользователя нет прав на удаление данного раздела!"):
            await sections_service.update_section(
                user=user,
                section_id=section_id,
                new_name="Новое имя",
                new_description=None,
                new_tags=None,
            )


class TestSwapSections:
    async def test_swaps_sections_successfully(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        first_section_id = uuid.uuid4()
        second_section_id = uuid.uuid4()
        same_course_id = uuid.uuid4()
        first_section = create_section_response_mock(
            section_id=first_section_id,
            course_id=same_course_id,
            order_number=1,
        )
        second_section = create_section_response_mock(
            section_id=second_section_id,
            course_id=same_course_id,
            order_number=2,
        )

        mock_sections_manager.get_section_by_id.side_effect = [first_section, second_section]
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS

        await sections_service.swap_sections(user, first_section_id, second_section_id)

        mock_sections_manager.swap_sections.assert_awaited_once_with(first_section_id, second_section_id)

    async def test_raises_error_when_courses_different(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        first_section = create_section_response_mock(course_id=uuid.uuid4())
        second_section = create_section_response_mock(course_id=uuid.uuid4())

        mock_sections_manager.get_section_by_id.side_effect = [first_section, second_section]

        with pytest.raises(DifferentSourcesContentSwapError, match="Обменяться порядковыми номерами "
                                                                   "между разделами можно только в "
                                                                   "пределах одного курса!"):
            await sections_service.swap_sections(user, uuid.uuid4(), uuid.uuid4())

    async def test_raises_error_when_no_edit_access(
        self,
        sections_service: SectionsService,
        mock_sections_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        same_course_id = uuid.uuid4()
        first_section = create_section_response_mock(course_id=same_course_id)
        second_section = create_section_response_mock(course_id=same_course_id)

        mock_sections_manager.get_section_by_id.side_effect = [first_section, second_section]
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="У пользователя нет прав на удаление данного раздела!"):
            await sections_service.swap_sections(user, uuid.uuid4(), uuid.uuid4())
