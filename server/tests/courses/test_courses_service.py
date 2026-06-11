import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from server.app.api.v1.courses.course_state import CourseState
from server.app.api.v1.courses.courses import (
    CourseFullListResponse,
    CourseIDMixin,
    CourseResponse,
    CoursesListSearchResponse,
)
from server.app.api.v1.courses.courses_service import CoursesService
from server.app.api.v1.exceptions import (
    BadRequestError,
    ConflictError,
    MediaTypeError,
    ObjectMissingError,
    OperationPermissionError,
)
from server.enums.access_permissions import AccessPermissions
from server.enums.role import Role

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_courses_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.get_courses_of_user = mocker.AsyncMock()
    manager.get_controlled_courses = mocker.AsyncMock()
    manager.create_course = mocker.AsyncMock()
    manager.get_course_by_id = mocker.AsyncMock()
    manager.update_course = mocker.AsyncMock()
    manager.delete_course = mocker.AsyncMock()
    manager.check_is_user_enrolled_on_course = mocker.AsyncMock()
    manager.search_courses_by_name_prefix = mocker.AsyncMock()
    manager.search_courses_by_tag = mocker.AsyncMock()
    manager.change_course_professor = mocker.AsyncMock()
    return manager


@pytest.fixture
def mock_auth_manager(mocker: MockerFixture):
    return mocker.AsyncMock()


@pytest.fixture
def mock_users_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.get_user_by_id = mocker.AsyncMock()
    return manager


@pytest.fixture
def mock_users_service(mocker: MockerFixture):
    service = mocker.AsyncMock()
    service.check_course_access = mocker.AsyncMock()
    return service


@pytest.fixture
def mock_courses_resources_manager(mocker: MockerFixture):
    manager = mocker.MagicMock()
    manager.create_course = mocker.MagicMock()
    manager.delete_course_directory = mocker.MagicMock()
    manager.set_course_icon = mocker.AsyncMock()
    manager.get_course_icon_path = mocker.MagicMock()
    return manager


@pytest.fixture
def courses_service(
    mock_courses_manager,
    mock_auth_manager,
    mock_users_manager,
    mock_users_service,
    mock_courses_resources_manager,
) -> CoursesService:
    return CoursesService(
        courses_manager=mock_courses_manager,
        auth_manager=mock_auth_manager,
        users_manager=mock_users_manager,
        users_service=mock_users_service,
        courses_resources_manager=mock_courses_resources_manager,
    )


def create_course_response_mock(
    course_id: uuid.UUID = None,
    name: str = "Test Course",
    description: str = "Description",
    professor_id: uuid.UUID = None,
    professor_name: str = "John",
    professor_surname: str = "Doe",
    professor_patronymic: str = "Smith",
    is_public: bool = True,
    is_content_public: bool = True,
    tags: list[str] = None,
) -> dict:
    return {
        "id": course_id or uuid.uuid4(),
        "name": name,
        "description": description,
        "professor_id": professor_id or uuid.uuid4(),
        "professor_name": professor_name,
        "professor_surname": professor_surname,
        "professor_patronymic": professor_patronymic,
        "is_public": is_public,
        "is_content_public": is_content_public,
        "tags": tags or [],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


class TestGetCoursesForUser:
    async def test_returns_courses_for_user(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        expected_response = CourseFullListResponse(root=[])
        mock_courses_manager.get_courses_of_user.return_value = expected_response

        result = await courses_service.get_courses_for_user(user, page=1, size=10)

        mock_courses_manager.get_courses_of_user.assert_awaited_once_with(
            user.id, 0, 10
        )
        assert result == expected_response

    async def test_pagination_calculates_offset_correctly(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)

        await courses_service.get_courses_for_user(user, page=3, size=15)

        mock_courses_manager.get_courses_of_user.assert_awaited_once_with(
            user.id, 30, 15
        )

    async def test_returns_empty_list_for_user_without_courses(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        expected_response = CourseFullListResponse(root=[])
        mock_courses_manager.get_courses_of_user.return_value = expected_response

        result = await courses_service.get_courses_for_user(user, page=1, size=10)

        assert result.root == []


class TestGetControlledCourses:
    async def test_returns_professor_courses(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        expected_response = CourseFullListResponse(root=[])
        mock_courses_manager.get_controlled_courses.return_value = expected_response

        result = await courses_service.get_controlled_courses(user, page=1, records_per_page=10)

        mock_courses_manager.get_controlled_courses.assert_awaited_once_with(
            user.id, 0, 10
        )
        assert result == expected_response

    async def test_pagination_calculates_offset_correctly(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)

        await courses_service.get_controlled_courses(user, page=2, records_per_page=5)

        mock_courses_manager.get_controlled_courses.assert_awaited_once_with(
            user.id, 5, 5
        )

    async def test_returns_empty_for_professor_without_courses(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        expected_response = CourseFullListResponse(root=[])
        mock_courses_manager.get_controlled_courses.return_value = expected_response

        result = await courses_service.get_controlled_courses(user, page=1, records_per_page=10)

        assert result.root == []


class TestCreateCourse:
    async def test_creates_course_for_professor(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_courses_resources_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        expected_course_id = uuid.uuid4()
        mock_courses_manager.create_course.return_value = CourseIDMixin(id=expected_course_id)

        result = await courses_service.create_course(
            user=user,
            name="Новый курс",
            description="Описание курса",
            is_public=True,
            is_content_public=True,
            tags=["python", "web"],
        )

        mock_courses_manager.create_course.assert_awaited_once_with(
            name="Новый курс",
            description="Описание курса",
            professor_id=user.id,
            is_public=True,
            is_content_public=True,
            tags=["python", "web"],
        )
        mock_courses_resources_manager.create_course.assert_called_once_with(
            expected_course_id
        )
        assert result.id == expected_course_id

    async def test_student_cannot_create_course(
        self,
        courses_service: CoursesService,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)

        with pytest.raises(OperationPermissionError, match="Обучающийся не имеет права на создание курса!"):
            await courses_service.create_course(
                user=user,
                name="Новый курс",
                description="Описание",
                is_public=True,
                is_content_public=True,
                tags=[],
            )

    async def test_cannot_create_course_with_content_public_but_course_private(
        self,
        courses_service: CoursesService,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)

        with pytest.raises(ConflictError, match="Содержимое курса не может быть публичным, если сам курс непубличный!"):
            await courses_service.create_course(
                user=user,
                name="Новый курс",
                description="Описание",
                is_public=False,
                is_content_public=True,
                tags=[],
            )


class TestGetCourseById:
    async def test_returns_course_for_professor_with_access(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        course_data = create_course_response_mock(course_id=course_id, professor_id=user.id)
        expected_course = CourseResponse.model_validate(course_data)
        mock_courses_manager.get_course_by_id.return_value = expected_course
        mock_users_service.check_course_access.return_value = AccessPermissions.HEADER_ACCESS

        result = await courses_service.get_course_by_id(user, course_id)

        mock_courses_manager.get_course_by_id.assert_awaited_once_with(course_id)
        mock_users_service.check_course_access.assert_awaited_once_with(user, course=expected_course)
        assert result.id == course_id

    async def test_returns_public_course_for_unauthorized_user(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
    ):
        course_id = uuid.uuid4()
        course_data = create_course_response_mock(course_id=course_id, is_public=True)
        expected_course = CourseResponse.model_validate(course_data)
        mock_courses_manager.get_course_by_id.return_value = expected_course
        mock_users_service.check_course_access.return_value = AccessPermissions.HEADER_ACCESS

        result = await courses_service.get_course_by_id(None, course_id)

        assert result.id == course_id

    async def test_returns_private_course_for_student_due_to_content_public(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        course_id = uuid.uuid4()
        course_data = create_course_response_mock(course_id=course_id, is_public=False, is_content_public=True)
        expected_course = CourseResponse.model_validate(course_data)
        mock_courses_manager.get_course_by_id.return_value = expected_course
        mock_users_service.check_course_access.return_value = AccessPermissions.CONTENT_ACCESS

        result = await courses_service.get_course_by_id(user, course_id)

        assert result.id == course_id

    async def test_raises_error_for_private_course_with_private_content(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        course_id = uuid.uuid4()
        course_data = create_course_response_mock(course_id=course_id, is_public=False, is_content_public=False)
        expected_course = CourseResponse.model_validate(course_data)
        mock_courses_manager.get_course_by_id.return_value = expected_course
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="Пользователь не имеет доступа к данному курсу!"):
            await courses_service.get_course_by_id(user, course_id)

    async def test_raises_error_when_course_not_found(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        mock_courses_manager.get_course_by_id.side_effect = ObjectMissingError("Курса с таким ID не существует!")

        with pytest.raises(ObjectMissingError, match="Курса с таким ID не существует!"):
            await courses_service.get_course_by_id(user, course_id)


class TestUpdateCourse:
    async def test_updates_course_fields(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        existing_course = MagicMock(
            name="Старое название",
            description="Старое описание",
            is_public=True,
            is_content_public=True,
            tags=["old"],
        )
        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS

        await courses_service.update_course(
            user=user,
            course_id=course_id,
            new_name="Новое название",
            new_description="Новое описание",
            new_is_public=False,
            new_is_content_public=False,
            new_tags=["new"],
        )

        mock_courses_manager.update_course.assert_awaited_once_with(
            course_id,
            "Новое название",
            "Новое описание",
            False,
            False,
            ["new"],
        )

    async def test_updates_only_specified_fields(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        existing_course = MagicMock(
            name="Старое название",
            description="Старое описание",
            is_public=True,
            is_content_public=True,
            tags=["old"],
        )
        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS

        await courses_service.update_course(
            user=user,
            course_id=course_id,
            new_name="Новое название",
            new_description=None,
            new_is_public=None,
            new_is_content_public=None,
            new_tags=None,
        )

        mock_courses_manager.update_course.assert_awaited_once_with(
            course_id,
            "Новое название",
            "Старое описание",
            True,
            True,
            ["old"],
        )

    async def test_no_changes_when_all_none(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        existing_course = MagicMock()
        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS

        await courses_service.update_course(
            user=user,
            course_id=course_id,
            new_name=None,
            new_description=None,
            new_is_public=None,
            new_is_content_public=None,
            new_tags=None,
        )

        mock_courses_manager.update_course.assert_not_awaited()

    async def test_student_cannot_update_course(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        course_id = uuid.uuid4()
        existing_course = MagicMock()
        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="У пользователя нет прав на изменение курса!"):
            await courses_service.update_course(
                user=user,
                course_id=course_id,
                new_name="Новое название",
                new_description=None,
                new_is_public=None,
                new_is_content_public=None,
                new_tags=None,
            )


class TestDeleteCourse:
    async def test_deletes_course(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
        mock_courses_resources_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        existing_course = MagicMock()
        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS

        await courses_service.delete_course(user, course_id)

        mock_courses_manager.delete_course.assert_awaited_once_with(course_id)
        mock_courses_resources_manager.delete_course_directory.assert_called_once_with(course_id)

    async def test_student_cannot_delete_course(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        course_id = uuid.uuid4()
        existing_course = MagicMock()
        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="У пользователя нет прав на удаление курса!"):
            await courses_service.delete_course(user, course_id)


class TestResolveCourseState:
    async def test_returns_controlled_for_professor(
        self,
        courses_service: CoursesService,
    ):
        user_id = uuid.uuid4()
        course = MagicMock(professor_id=user_id, is_public=True)

        state = await courses_service.resolve_course_state(user_id, course)

        assert state == CourseState.CONTROLLED

    async def test_returns_enrolled_for_enrolled_student(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user_id = uuid.uuid4()
        course_id = uuid.uuid4()
        course = MagicMock(professor_id=uuid.uuid4(), id=course_id, is_public=False)
        mock_courses_manager.check_is_user_enrolled_on_course.return_value = True

        state = await courses_service.resolve_course_state(user_id, course)

        mock_courses_manager.check_is_user_enrolled_on_course.assert_awaited_once_with(user_id, course_id)
        assert state == CourseState.ENROLLED

    async def test_returns_enrollable_for_public_course(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user_id = uuid.uuid4()
        course = MagicMock(professor_id=uuid.uuid4(), is_public=True)
        mock_courses_manager.check_is_user_enrolled_on_course.return_value = False

        state = await courses_service.resolve_course_state(user_id, course)

        assert state == CourseState.ENROLLABLE

    async def test_returns_none_for_private_course_not_enrolled(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user_id = uuid.uuid4()
        course = MagicMock(professor_id=uuid.uuid4(), is_public=False)
        mock_courses_manager.check_is_user_enrolled_on_course.return_value = False

        state = await courses_service.resolve_course_state(user_id, course)

        assert state is None

    async def test_returns_enrollable_for_unauthenticated_user_on_public_course(
        self,
        courses_service: CoursesService,
    ):
        course = MagicMock(is_public=True)

        state = await courses_service.resolve_course_state(None, course)

        assert state == CourseState.ENROLLABLE

    async def test_returns_none_for_unauthenticated_user_on_private_course(
        self,
        courses_service: CoursesService,
    ):
        course = MagicMock(is_public=False)

        state = await courses_service.resolve_course_state(None, course)

        assert state is None


class TestSearchCourses:
    async def test_search_by_name_prefix(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course1_data = create_course_response_mock(name="Алгоритмы")
        course2_data = create_course_response_mock(name="Алгебра")
        course1 = CourseResponse.model_validate(course1_data)
        course2 = CourseResponse.model_validate(course2_data)
        searched_response = CourseFullListResponse(root=[course1, course2])
        mock_courses_manager.search_courses_by_name_prefix.return_value = searched_response

        result = await courses_service.search_courses(
            user=user,
            criteria="name_prefix",
            value="Алг",
            page=1,
            records_per_page=10,
        )

        mock_courses_manager.search_courses_by_name_prefix.assert_awaited_once_with("Алг")
        assert isinstance(result, CoursesListSearchResponse)
        assert len(result.root) == 2

    async def test_search_by_tag(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_data = create_course_response_mock(name="Курс")
        course = CourseResponse.model_validate(course_data)
        searched_response = CourseFullListResponse(root=[course])
        mock_courses_manager.search_courses_by_tag.return_value = searched_response

        result = await courses_service.search_courses(
            user=user,
            criteria="tag",
            value="python",
            page=1,
            records_per_page=10,
        )

        mock_courses_manager.search_courses_by_tag.assert_awaited_once_with("python")
        assert isinstance(result, CoursesListSearchResponse)
        assert len(result.root) == 1

    async def test_search_pagination(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        courses_data = [create_course_response_mock(name=f"Курс {i}") for i in range(5)]
        courses = [CourseResponse.model_validate(data) for data in courses_data]
        searched_response = CourseFullListResponse(root=courses)
        mock_courses_manager.search_courses_by_name_prefix.return_value = searched_response

        result_page1 = await courses_service.search_courses(
            user=user,
            criteria="name_prefix",
            value="Курс",
            page=1,
            records_per_page=2,
        )
        result_page2 = await courses_service.search_courses(
            user=user,
            criteria="name_prefix",
            value="Курс",
            page=2,
            records_per_page=2,
        )

        assert len(result_page1.root) == 2
        assert len(result_page2.root) == 2

    async def test_raises_error_for_unsupported_criteria(
        self,
        courses_service: CoursesService,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)

        with pytest.raises(BadRequestError, match="Неподдерживаемый критерий: invalid"):
            await courses_service.search_courses(
                user=user,
                criteria="invalid",
                value="test",
                page=1,
                records_per_page=10,
            )

    async def test_filters_courses_by_state_for_unauthenticated_user(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
    ):
        public_course_data = create_course_response_mock(name="Публичный курс", is_public=True)
        private_course_data = create_course_response_mock(name="Приватный курс", is_public=False)
        public_course = CourseResponse.model_validate(public_course_data)
        private_course = CourseResponse.model_validate(private_course_data)
        searched_response = CourseFullListResponse(root=[public_course, private_course])
        mock_courses_manager.search_courses_by_name_prefix.return_value = searched_response

        result = await courses_service.search_courses(
            user=None,
            criteria="name_prefix",
            value="курс",
            page=1,
            records_per_page=10,
        )

        assert len(result.root) == 1
        assert result.root[0].name == "Публичный курс"


class TestChangeCourseProfessor:
    async def test_changes_professor_successfully(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        new_professor_id = uuid.uuid4()
        existing_course = MagicMock()
        new_professor = MagicMock(role=Role.PROFESSOR)

        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS
        mock_users_manager.get_user_by_id.return_value = new_professor

        await courses_service.change_course_professor(
            user=user,
            course_id=course_id,
            new_professor_id=new_professor_id,
        )

        mock_courses_manager.change_course_professor.assert_awaited_once_with(course_id, new_professor_id)

    async def test_raises_error_when_no_edit_access(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        course_id = uuid.uuid4()
        existing_course = MagicMock()
        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="У пользователя нет прав на передачу владения курсом!"):
            await courses_service.change_course_professor(
                user=user,
                course_id=course_id,
                new_professor_id=uuid.uuid4(),
            )

    async def test_raises_error_when_new_professor_not_exists(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        existing_course = MagicMock()
        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS
        mock_users_manager.get_user_by_id.return_value = None

        with pytest.raises(ObjectMissingError, match="Не найден пользователь с идентификатором нового преподавателя!"):
            await courses_service.change_course_professor(
                user=user,
                course_id=course_id,
                new_professor_id=uuid.uuid4(),
            )

    async def test_raises_error_when_new_professor_is_student(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        existing_course = MagicMock()
        new_professor = MagicMock(role=Role.STUDENT)

        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS
        mock_users_manager.get_user_by_id.return_value = new_professor

        with pytest.raises(OperationPermissionError, match="У нового преподавателя нет права на ведение курса!"):
            await courses_service.change_course_professor(
                user=user,
                course_id=course_id,
                new_professor_id=uuid.uuid4(),
            )


class TestSetCourseIcon:
    async def test_sets_course_icon_successfully(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
        mock_courses_resources_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        existing_course = MagicMock()
        icon_file = MagicMock(content_type="image/png")

        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.EDIT_ACCESS
        mock_courses_resources_manager.set_course_icon.return_value = None

        await courses_service.set_course_icon(user, course_id, icon_file)

        mock_courses_resources_manager.set_course_icon.assert_awaited_once_with(course_id, icon_file)

    async def test_raises_error_when_file_type_not_image(
        self,
        courses_service: CoursesService,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        icon_file = MagicMock(content_type="application/pdf")

        with pytest.raises(MediaTypeError, match="Некорректный тип файла!"):
            await courses_service.set_course_icon(user, course_id, icon_file)

    async def test_raises_error_when_no_edit_access(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        course_id = uuid.uuid4()
        existing_course = MagicMock()
        icon_file = MagicMock(content_type="image/png")

        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="У пользователя нет прав на установку иконки курса!"):
            await courses_service.set_course_icon(user, course_id, icon_file)


class TestGetCourseIconPath:
    async def test_returns_icon_path(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
        mock_courses_resources_manager,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.PROFESSOR)
        course_id = uuid.uuid4()
        existing_course = MagicMock()
        expected_path = "/path/to/icon.png"

        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.HEADER_ACCESS
        mock_courses_resources_manager.get_course_icon_path.return_value = expected_path

        result = await courses_service.get_course_icon_path(user, course_id)

        assert result == expected_path

    async def test_raises_error_when_no_header_access(
        self,
        courses_service: CoursesService,
        mock_courses_manager,
        mock_users_service,
    ):
        user = MagicMock(id=uuid.uuid4(), role=Role.STUDENT)
        course_id = uuid.uuid4()
        existing_course = MagicMock()
        mock_courses_manager.get_course_by_id.return_value = existing_course
        mock_users_service.check_course_access.return_value = AccessPermissions.NO_ACCESS

        with pytest.raises(OperationPermissionError, match="У пользователя нет прав на просмотр иконки курса!"):
            await courses_service.get_course_icon_path(user, course_id)
