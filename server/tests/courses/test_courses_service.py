import uuid
from unittest.mock import MagicMock

import pytest

from server.app.api.v1.courses.course_state import CourseState
from server.app.api.v1.courses.courses import (
    CourseFullListResponse,
    CourseIDMixin,
    CoursesListSearchResponse,
)
from server.app.api.v1.exceptions import (
    BadRequestError,
    ConflictError,
    ObjectMissingError,
    OperationPermissionError,
)
from server.enums.role import Role

pytestmark = pytest.mark.asyncio


class TestGetCoursesForUser:
    async def test_returns_courses_for_user(
            self,
            courses_service,
            professor_factory,
            course_factory,
            enrollment_factory,
            student_factory,
    ):
        professor = await professor_factory()
        course1 = await course_factory(name="Курс 1", professor_id=professor.id)
        course2 = await course_factory(name="Курс 2", professor_id=professor.id)
        student = await student_factory()

        await enrollment_factory(student_id=student.id, course_id=course1.id)
        await enrollment_factory(student_id=student.id, course_id=course2.id)

        user = MagicMock()
        user.id = student.id
        user.role = Role.STUDENT

        result = await courses_service.get_courses_for_user(user, page=1, size=10)

        assert isinstance(result, CourseFullListResponse)
        assert len(result.root) == 2

    async def test_pagination_works(
            self,
            courses_service,
            professor_factory,
            course_factory,
            enrollment_factory,
            student_factory,
    ):
        professor = await professor_factory()
        student = await student_factory()

        for i in range(5):
            course = await course_factory(name=f"Курс {i}", professor_id=professor.id)
            await enrollment_factory(student_id=student.id, course_id=course.id)

        user = MagicMock()
        user.id = student.id
        user.role = Role.STUDENT

        result_page1 = await courses_service.get_courses_for_user(user, page=1, size=2)
        result_page2 = await courses_service.get_courses_for_user(user, page=2, size=2)

        assert len(result_page1.root) == 2
        assert len(result_page2.root) == 2

    async def test_returns_empty_list_for_user_without_courses(
            self,
            courses_service,
            student_factory,
    ):
        student = await student_factory()

        user = MagicMock()
        user.id = student.id
        user.role = Role.STUDENT

        result = await courses_service.get_courses_for_user(user, page=1, size=10)
        assert result.root == []


class TestGetControlledCourses:
    async def test_returns_professor_courses(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        other_professor = await professor_factory(name="Другой", surname="Проф")

        my_course = await course_factory(name="Мой курс", professor_id=professor.id)
        await course_factory(name="Чужой курс", professor_id=other_professor.id)

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        result = await courses_service.get_controlled_courses(user, page=1, records_per_page=10)

        assert isinstance(result, CourseFullListResponse)
        assert len(result.root) == 1
        assert result.root[0].id == my_course.id

    async def test_returns_empty_for_professor_without_courses(
            self,
            courses_service,
            professor_factory,
    ):
        professor = await professor_factory()

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        result = await courses_service.get_controlled_courses(user, page=1, records_per_page=10)
        assert result.root == []

    async def test_pagination_works_for_controlled_courses(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()

        for i in range(5):
            await course_factory(name=f"Курс {i}", professor_id=professor.id)

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        result_page1 = await courses_service.get_controlled_courses(user, page=1, records_per_page=2)
        result_page2 = await courses_service.get_controlled_courses(user, page=2, records_per_page=2)

        assert len(result_page1.root) == 2
        assert len(result_page2.root) == 2


class TestCreateCourse:
    async def test_creates_course_for_professor(
            self,
            courses_service,
            professor_factory,
    ):
        professor = await professor_factory()

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        result = await courses_service.create_course(
            user=user,
            name="Новый курс",
            description="Описание курса",
            is_public=True,
            is_content_public=True,
            tags=["python", "web"],
        )

        assert isinstance(result, CourseIDMixin)
        assert result.id is not None

    async def test_student_cannot_create_course(
            self,
            courses_service,
            student_factory,
    ):
        student = await student_factory()

        user = MagicMock()
        user.id = student.id
        user.role = Role.STUDENT

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
            courses_service,
            professor_factory,
    ):
        professor = await professor_factory()

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

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
    async def test_returns_course_for_professor(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        course = await course_factory(professor_id=professor.id)

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        result = await courses_service.get_course_by_id(user, course.id)
        assert result.id == course.id

    async def test_returns_public_course_for_unauthorized_user(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        course = await course_factory(professor_id=professor.id, is_public=True)

        result = await courses_service.get_course_by_id(None, course.id)
        assert result.id == course.id

    async def test_returns_private_course_for_student_due_to_content_public(
            self,
            courses_service,
            professor_factory,
            course_factory,
            student_factory,
    ):
        professor = await professor_factory()
        private_course = await course_factory(
            professor_id=professor.id,
            is_public=False,
            is_content_public=True,
            name="Приватный курс с публичным контентом"
        )

        student = await student_factory()

        user = MagicMock()
        user.id = student.id
        user.role = Role.STUDENT

        result = await courses_service.get_course_by_id(user, private_course.id)
        assert result.id == private_course.id

    async def test_raises_error_for_private_course_with_private_content(
            self,
            courses_service,
            professor_factory,
            course_factory,
            student_factory,
    ):
        professor = await professor_factory()
        private_course = await course_factory(
            professor_id=professor.id,
            is_public=False,
            is_content_public=False,  # Контент тоже приватный
            name="Полностью приватный курс"
        )

        student = await student_factory()

        user = MagicMock()
        user.id = student.id
        user.role = Role.STUDENT

        with pytest.raises(OperationPermissionError, match="Пользователь не имеет доступа к данному курсу!"):
            await courses_service.get_course_by_id(user, private_course.id)

    async def test_raises_error_when_course_not_found(
            self,
            courses_service,
            professor_factory,
    ):
        professor = await professor_factory()

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        with pytest.raises(ObjectMissingError, match="Курса с таким ID не существует!"):
            await courses_service.get_course_by_id(user, uuid.uuid4())


class TestUpdateCourse:
    async def test_updates_course_fields(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        course = await course_factory(professor_id=professor.id)

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        await courses_service.update_course(
            user=user,
            course_id=course.id,
            new_name="Обновлённое название",
            new_description="Новое описание",
            new_is_public=False,
            new_is_content_public=False,
            new_tags=["updated"],
        )

        updated = await courses_service.get_course_by_id(user, course.id)
        assert updated.name == "Обновлённое название"

    async def test_updates_only_specified_fields(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        course = await course_factory(
            professor_id=professor.id,
            name="Старое название",
            description="Старое описание",
            tags=["old"],
        )

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        await courses_service.update_course(
            user=user,
            course_id=course.id,
            new_name="Новое название",
            new_description=None,
            new_is_public=None,
            new_is_content_public=None,
            new_tags=None,
        )

        updated = await courses_service.get_course_by_id(user, course.id)
        assert updated.name == "Новое название"
        assert updated.description == "Старое описание"

    async def test_no_changes_when_all_none(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        course = await course_factory(professor_id=professor.id)

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        await courses_service.update_course(
            user=user,
            course_id=course.id,
            new_name=None,
            new_description=None,
            new_is_public=None,
            new_is_content_public=None,
            new_tags=None,
        )

        updated = await courses_service.get_course_by_id(user, course.id)
        assert updated.name == course.name

    async def test_student_cannot_update_course(
            self,
            courses_service,
            professor_factory,
            course_factory,
            student_factory,
    ):
        professor = await professor_factory()
        course = await course_factory(professor_id=professor.id)
        student = await student_factory()

        user = MagicMock()
        user.id = student.id
        user.role = Role.STUDENT

        with pytest.raises(OperationPermissionError, match="У пользователя нет прав на изменение курса!"):
            await courses_service.update_course(
                user=user,
                course_id=course.id,
                new_name="Новое название",
                new_description=None,
                new_is_public=None,
                new_is_content_public=None,
                new_tags=None,
            )


class TestDeleteCourse:
    async def test_deletes_course(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        course = await course_factory(professor_id=professor.id)

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        await courses_service.delete_course(user, course.id)

        with pytest.raises(ObjectMissingError):
            await courses_service.get_course_by_id(user, course.id)

    async def test_student_cannot_delete_course(
            self,
            courses_service,
            professor_factory,
            course_factory,
            student_factory,
    ):
        professor = await professor_factory()
        course = await course_factory(professor_id=professor.id)
        student = await student_factory()

        user = MagicMock()
        user.id = student.id
        user.role = Role.STUDENT

        with pytest.raises(OperationPermissionError, match="У пользователя нет прав на удаление курса!"):
            await courses_service.delete_course(user, course.id)


class TestResolveCourseState:
    async def test_returns_controlled_for_professor(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        course = await course_factory(professor_id=professor.id)

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        course_response = await courses_service.get_course_by_id(user, course.id)
        state = await courses_service.resolve_course_state(professor.id, course_response)

        assert state == CourseState.CONTROLLED

    async def test_returns_enrolled_for_enrolled_student(
            self,
            courses_service,
            professor_factory,
            course_factory,
            enrollment_factory,
            student_factory,
    ):
        professor = await professor_factory()
        course = await course_factory(professor_id=professor.id)
        student = await student_factory()

        await enrollment_factory(student_id=student.id, course_id=course.id)

        course_response = await courses_service.get_course_by_id(None, course.id)
        state = await courses_service.resolve_course_state(student.id, course_response)

        assert state == CourseState.ENROLLED

    async def test_returns_enrollable_for_public_course(
            self,
            courses_service,
            professor_factory,
            course_factory,
            student_factory,
    ):
        professor = await professor_factory()
        course = await course_factory(professor_id=professor.id, is_public=True)
        student = await student_factory()

        course_response = await courses_service.get_course_by_id(None, course.id)
        state = await courses_service.resolve_course_state(student.id, course_response)

        assert state == CourseState.ENROLLABLE


class TestSearchCourses:
    async def test_search_by_name_prefix(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        await course_factory(name="Алгоритмы", professor_id=professor.id)
        await course_factory(name="Алгебра", professor_id=professor.id)
        await course_factory(name="Базы данных", professor_id=professor.id)

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        result = await courses_service.search_courses(
            user=user,
            criteria="name_prefix",
            value="Алг",
            page=1,
            records_per_page=10,
        )

        assert isinstance(result, CoursesListSearchResponse)
        assert len(result.root) == 2
        names = [c.name for c in result.root]
        assert "Алгоритмы" in names
        assert "Алгебра" in names

    async def test_search_by_tag(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        await course_factory(professor_id=professor.id, tags=["python", "web"])
        await course_factory(professor_id=professor.id, tags=["java"])
        await course_factory(professor_id=professor.id, tags=["python", "data"])

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        result = await courses_service.search_courses(
            user=user,
            criteria="tag",
            value="python",
            page=1,
            records_per_page=10,
        )

        assert len(result.root) == 2

    async def test_search_pagination(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        for i in range(5):
            await course_factory(name=f"Курс {i}", professor_id=professor.id)

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

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
            courses_service,
            professor_factory,
    ):
        professor = await professor_factory()

        user = MagicMock()
        user.id = professor.id
        user.role = Role.PROFESSOR

        with pytest.raises(BadRequestError, match="Неподдерживаемый критерий: invalid"):
            await courses_service.search_courses(
                user=user,
                criteria="invalid",
                value="test",
                page=1,
                records_per_page=10,
            )


class TestChangeCourseProfessor:
    async def test_changes_professor_successfully(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        old_professor = await professor_factory()
        course = await course_factory(professor_id=old_professor.id)
        new_professor = await professor_factory(name="Новый", surname="Преподаватель")

        user = MagicMock()
        user.id = old_professor.id
        user.role = Role.PROFESSOR

        await courses_service.change_course_professor(
            user=user,
            course_id=course.id,
            new_professor_id=new_professor.id,
        )

        updated = await courses_service.get_course_by_id(user, course.id)
        assert updated.professor_id == new_professor.id

    async def test_raises_error_when_new_professor_not_exists(
            self,
            courses_service,
            professor_factory,
            course_factory,
    ):
        old_professor = await professor_factory()
        course = await course_factory(professor_id=old_professor.id)

        user = MagicMock()
        user.id = old_professor.id
        user.role = Role.PROFESSOR

        with pytest.raises(ObjectMissingError, match="Не найден пользователь с идентификатором нового преподавателя!"):
            await courses_service.change_course_professor(
                user=user,
                course_id=course.id,
                new_professor_id=uuid.uuid4(),
            )

    async def test_raises_error_when_new_professor_is_student(
            self,
            courses_service,
            professor_factory,
            course_factory,
            student_factory,
    ):
        old_professor = await professor_factory()
        course = await course_factory(professor_id=old_professor.id)
        student = await student_factory()

        user = MagicMock()
        user.id = old_professor.id
        user.role = Role.PROFESSOR

        with pytest.raises(OperationPermissionError, match="У нового преподавателя нет права на ведение курса!"):
            await courses_service.change_course_professor(
                user=user,
                course_id=course.id,
                new_professor_id=student.id,
            )
