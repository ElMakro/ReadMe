import uuid

import pytest

from server.app.api.v1.exceptions import ObjectMissingError

pytestmark = pytest.mark.asyncio


class TestGetCourseById:
    async def test_returns_course_when_exists(
            self,
            courses_manager,
            setup_professor_and_course,
    ):
        professor, course = setup_professor_and_course
        result = await courses_manager.get_course_by_id(course.id)
        assert result.id == course.id
        assert result.name == course.name
        assert result.professor_id == professor.id

    async def test_raises_when_not_found(
            self,
            courses_manager,
    ):
        with pytest.raises(ObjectMissingError, match="Курса с таким ID не существует!"):
            await courses_manager.get_course_by_id(uuid.uuid4())

    async def test_returns_correct_tags(
            self,
            courses_manager,
            setup_professor_and_course,
    ):
        _, course = setup_professor_and_course
        result = await courses_manager.get_course_by_id(course.id)
        assert result.tags == course.tags


class TestCreateCourse:
    async def test_creates_and_returns_id(
            self,
            courses_manager,
            professor_factory,
    ):
        professor = await professor_factory()
        result = await courses_manager.create_course(
            name="Введение в машинное обучение",
            description="Машинное обучение",
            professor_id=professor.id,
            is_public=True,
            is_content_public=True,
            tags=["ml", "python"],
        )
        assert result.id is not None
        assert isinstance(result.id, uuid.UUID)

    async def test_created_course_is_fetchable(
            self,
            courses_manager,
            professor_factory,
    ):
        professor = await professor_factory()
        created = await courses_manager.create_course(
            name="Базы данных",
            description="SQL и NoSQL",
            professor_id=professor.id,
            is_public=False,
            is_content_public=False,
            tags=["db"],
        )

        fetched = await courses_manager.get_course_by_id(created.id)
        assert fetched.name == "Базы данных"
        assert fetched.description == "SQL и NoSQL"
        assert fetched.is_public is False
        assert fetched.is_content_public is False
        assert fetched.tags == ["db"]
        assert fetched.professor_id == professor.id

    async def test_empty_tags_allowed(
            self,
            courses_manager,
            professor_factory,
    ):
        professor = await professor_factory()
        created = await courses_manager.create_course(
            name="Без тегов",
            description="—",
            professor_id=professor.id,
            is_public=True,
            is_content_public=True,
            tags=[],
        )

        fetched = await courses_manager.get_course_by_id(created.id)
        assert fetched.tags == []


class TestGetCoursesOfUser:
    async def test_returns_enrolled_courses(
            self,
            courses_manager,
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

        result = await courses_manager.get_courses_of_user(student.id, offset=0, limit=10)

        assert len(result.root) == 2
        course_ids = {c.id for c in result.root}
        assert course1.id in course_ids
        assert course2.id in course_ids

    async def test_does_not_return_non_enrolled_courses(
            self,
            courses_manager,
            professor_factory,
            course_factory,
            enrollment_factory,
            student_factory,
    ):
        professor = await professor_factory()
        enrolled_course = await course_factory(name="Записан", professor_id=professor.id)
        other_course = await course_factory(name="Не записан", professor_id=professor.id)
        student = await student_factory()

        await enrollment_factory(student_id=student.id, course_id=enrolled_course.id)

        result = await courses_manager.get_courses_of_user(student.id, offset=0, limit=10)

        assert len(result.root) == 1
        assert result.root[0].id == enrolled_course.id
        assert result.root[0].id != other_course.id

    async def test_pagination_offset_and_limit(
            self,
            courses_manager,
            professor_factory,
            course_factory,
            enrollment_factory,
            student_factory,
    ):
        professor = await professor_factory()
        student = await student_factory()

        courses = []
        for i in range(5):
            course = await course_factory(name=f"Курс {i}", professor_id=professor.id)
            courses.append(course)
            await enrollment_factory(student_id=student.id, course_id=course.id)

        result_page1 = await courses_manager.get_courses_of_user(student.id, offset=0, limit=2)
        result_page2 = await courses_manager.get_courses_of_user(student.id, offset=2, limit=2)

        assert len(result_page1.root) == 2
        assert len(result_page2.root) == 2

        page1_ids = {c.id for c in result_page1.root}
        page2_ids = {c.id for c in result_page2.root}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_returns_empty_for_unknown_student(
            self,
            courses_manager,
    ):
        result = await courses_manager.get_courses_of_user(uuid.uuid4(), offset=0, limit=10)
        assert result.root == []


class TestGetControlledCourses:
    async def test_returns_professor_courses(
            self,
            courses_manager,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        other_professor = await professor_factory(name="Другой", surname="Проф")

        my_course = await course_factory(name="Мой курс", professor_id=professor.id)
        await course_factory(name="Чужой курс", professor_id=other_professor.id)

        result = await courses_manager.get_controlled_courses(professor.id, offset=0, limit=10)

        assert len(result.root) == 1
        assert result.root[0].id == my_course.id
        assert result.root[0].name == "Мой курс"

    async def test_returns_empty_for_professor_without_courses(
            self,
            courses_manager,
            professor_factory,
    ):
        professor = await professor_factory()
        result = await courses_manager.get_controlled_courses(professor.id, offset=0, limit=10)
        assert result.root == []


class TestUpdateCourse:
    async def test_updates_fields(
            self,
            courses_manager,
            setup_professor_and_course,
    ):
        _, course = setup_professor_and_course

        await courses_manager.update_course(
            course_id=course.id,
            name="Новое название",
            description="Новое описание",
            is_public=False,
            is_content_public=True,
            tags=["новый_тег"],
        )

        updated = await courses_manager.get_course_by_id(course.id)
        assert updated.name == "Новое название"
        assert updated.description == "Новое описание"
        assert updated.is_public is False
        assert updated.is_content_public is True
        assert updated.tags == ["новый_тег"]

    async def test_update_replaces_tags_completely(
            self,
            courses_manager,
            setup_professor_and_course,
    ):
        _, course = setup_professor_and_course

        await courses_manager.update_course(
            course_id=course.id,
            name=course.name,
            description=course.description,
            is_public=course.is_public,
            is_content_public=course.is_content_public,
            tags=["старый_тег1", "старый_тег2"],
        )

        # Затем очищаем их
        await courses_manager.update_course(
            course_id=course.id,
            name=course.name,
            description=course.description,
            is_public=course.is_public,
            is_content_public=course.is_content_public,
            tags=[],
        )

        updated = await courses_manager.get_course_by_id(course.id)
        assert updated.tags == []


class TestDeleteCourse:
    async def test_deletes_course(
            self,
            courses_manager,
            setup_professor_and_course,
    ):
        _, course = setup_professor_and_course
        course_id = course.id

        await courses_manager.delete_course(course_id)

        with pytest.raises(ObjectMissingError, match="Курса с таким ID не существует!"):
            await courses_manager.get_course_by_id(course_id)


class TestCheckIsUserEnrolled:
    async def test_returns_true_when_enrolled(
            self,
            courses_manager,
            setup_professor_and_course,
            enrollment_factory,
            student_factory,
    ):
        _, course = setup_professor_and_course
        student = await student_factory()
        await enrollment_factory(student_id=student.id, course_id=course.id)

        result = await courses_manager.check_is_user_enrolled_on_course(student.id, course.id)
        assert result is True

    async def test_returns_false_when_not_enrolled(
            self,
            courses_manager,
            setup_professor_and_course,
            student_factory,
    ):
        _, course = setup_professor_and_course
        student = await student_factory()

        result = await courses_manager.check_is_user_enrolled_on_course(student.id, course.id)
        assert result is False


class TestSearchCoursesByNamePrefix:
    async def test_finds_by_prefix(
            self,
            courses_manager,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        await course_factory(name="Алгоритмы и структуры данных", professor_id=professor.id)
        await course_factory(name="Алгебра и геометрия", professor_id=professor.id)
        await course_factory(name="Базы данных", professor_id=professor.id)

        result = await courses_manager.search_courses_by_name_prefix("Алг")

        names = [c.name for c in result.root]
        assert len(names) == 2
        assert "Алгоритмы и структуры данных" in names
        assert "Алгебра и геометрия" in names
        assert "Базы данных" not in names

    async def test_case_insensitive(
            self,
            courses_manager,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        await course_factory(name="Программирование на Python", professor_id=professor.id)

        result = await courses_manager.search_courses_by_name_prefix("программирование")

        assert len(result.root) >= 1
        assert result.root[0].name == "Программирование на Python"

    async def test_returns_empty_when_no_match(
            self,
            courses_manager,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        await course_factory(name="Физика", professor_id=professor.id)

        result = await courses_manager.search_courses_by_name_prefix("Химия")
        assert result.root == []


class TestSearchCoursesByTag:
    async def test_finds_by_exact_tag(
            self,
            courses_manager,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        await course_factory(
            name="Введение в машинное обучение", professor_id=professor.id, tags=["ml", "python"]
        )
        await course_factory(
            name="Базы данных", professor_id=professor.id, tags=["database", "sql"]
        )

        result = await courses_manager.search_courses_by_tag("ml")

        names = [c.name for c in result.root]
        assert "Введение в машинное обучение" in names
        assert len(names) == 1

    async def test_returns_empty_for_unknown_tag(
            self,
            courses_manager,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        await course_factory(
            name="Курс с тегом", professor_id=professor.id, tags=["existing"]
        )

        result = await courses_manager.search_courses_by_tag("nonexistent_tag_xyz")
        assert result.root == []

    async def test_multiple_courses_with_same_tag(
            self,
            courses_manager,
            professor_factory,
            course_factory,
    ):
        professor = await professor_factory()
        await course_factory(
            name="Курс A", professor_id=professor.id, tags=["common", "extra"]
        )
        await course_factory(
            name="Курс B", professor_id=professor.id, tags=["common"]
        )

        result = await courses_manager.search_courses_by_tag("common")

        names = [c.name for c in result.root]
        assert len(names) == 2
        assert "Курс A" in names
        assert "Курс B" in names


class TestChangeCourseProfessor:
    async def test_changes_professor(
            self,
            courses_manager,
            professor_factory,
            setup_professor_and_course,
    ):
        old_professor, course = setup_professor_and_course
        new_professor = await professor_factory(name="Новый", surname="Профессор")

        assert old_professor.id != new_professor.id

        await courses_manager.change_course_professor(
            course_id=course.id,
            new_professor_id=new_professor.id,
        )

        updated = await courses_manager.get_course_by_id(course.id)
        assert updated.professor_id == new_professor.id
        assert updated.professor_id != old_professor.id
