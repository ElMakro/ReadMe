import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from server.app.api.v1.exceptions import BadRequestError, ObjectMissingError
from server.app.api.v1.sections.sections_manager import DifferentSourcesContentSwapError

pytestmark = pytest.mark.asyncio


class TestCreateSection:
    async def test_creates_section_and_returns_id(
        self,
        sections_manager,
        course_factory,
    ):
        # Сначала создаём курс
        course = await course_factory()

        result = await sections_manager.create_section(
            course_id=course.id,
            name="Новый раздел",
            description="Описание раздела",
            order_number=1,
            tags=["python", "basics"],
        )

        assert result.id is not None

        section = await sections_manager.get_section_by_id(result.id)
        assert section.name == "Новый раздел"
        assert section.description == "Описание раздела"
        assert section.order_number == 1
        assert section.tags == ["python", "basics"]
        assert section.course_id == course.id

    async def test_creates_section_with_empty_tags(
        self,
        sections_manager,
        course_factory,
    ):
        course = await course_factory()

        result = await sections_manager.create_section(
            course_id=course.id,
            name="Без тегов",
            description="",
            order_number=2,
            tags=[],
        )

        section = await sections_manager.get_section_by_id(result.id)
        assert section.tags == []

    async def test_cannot_create_section_without_course(
        self,
        sections_manager,
    ):
        # Попытка создать раздел без существующего курса должна вызвать ошибку
        with pytest.raises(IntegrityError):
            await sections_manager.create_section(
                course_id=uuid.uuid4(),
                name="Раздел без курса",
                description="",
                order_number=1,
                tags=[],
            )


class TestCheckCourseHaveSectionWithOrderNumber:
    async def test_returns_false_when_no_section(
        self,
        sections_manager,
        course_factory,
    ):
        course = await course_factory()

        result = await sections_manager.check_course_have_section_with_order_number(
            course.id, 999
        )
        assert result is False

    async def test_returns_true_when_section_exists(
        self,
        sections_manager,
        course_factory,
    ):
        course = await course_factory()
        await sections_manager.create_section(
            course_id=course.id,
            name="Раздел",
            description="",
            order_number=5,
            tags=[],
        )

        result = await sections_manager.check_course_have_section_with_order_number(
            course.id, 5
        )
        assert result is True


class TestGetSectionsByCourseId:
    async def test_returns_sections_ordered_by_order_number(
        self,
        sections_manager,
        course_factory,
    ):
        course = await course_factory()

        await sections_manager.create_section(course.id, "Раздел 1", "", 3, [])
        await sections_manager.create_section(course.id, "Раздел 2", "", 1, [])
        await sections_manager.create_section(course.id, "Раздел 3", "", 2, [])

        result = await sections_manager.get_sections_by_course_id(course.id)

        assert len(result.root) == 3
        order_numbers = [s.order_number for s in result.root]
        assert order_numbers == [1, 2, 3]

    async def test_returns_empty_list_for_course_without_sections(
        self,
        sections_manager,
        course_factory,
    ):
        course = await course_factory()

        result = await sections_manager.get_sections_by_course_id(course.id)
        assert result.root == []

    async def test_returns_only_sections_from_specific_course(
        self,
        sections_manager,
        course_factory,
    ):
        course1 = await course_factory(name="Курс 1")
        course2 = await course_factory(name="Курс 2")

        await sections_manager.create_section(course1.id, "Раздел курса 1", "", 1, [])
        await sections_manager.create_section(course2.id, "Раздел курса 2", "", 1, [])

        result1 = await sections_manager.get_sections_by_course_id(course1.id)
        result2 = await sections_manager.get_sections_by_course_id(course2.id)

        assert len(result1.root) == 1
        assert result1.root[0].name == "Раздел курса 1"
        assert len(result2.root) == 1
        assert result2.root[0].name == "Раздел курса 2"


class TestGetSectionById:
    async def test_returns_section_when_exists(
        self,
        sections_manager,
        course_factory,
    ):
        course = await course_factory()
        created = await sections_manager.create_section(
            course_id=course.id,
            name="Тестовый раздел",
            description="Описание",
            order_number=1,
            tags=["test"],
        )

        section = await sections_manager.get_section_by_id(created.id)

        assert section.id == created.id
        assert section.name == "Тестовый раздел"
        assert section.course_id == course.id

    async def test_raises_error_when_not_found(
        self,
        sections_manager,
    ):
        with pytest.raises(ObjectMissingError, match="Раздела курса с таким идентификатором не существует!"):
            await sections_manager.get_section_by_id(uuid.uuid4())


class TestUpdateSection:
    async def test_updates_all_fields(
        self,
        sections_manager,
        course_factory,
    ):
        course = await course_factory()
        created = await sections_manager.create_section(
            course_id=course.id,
            name="Старое название",
            description="Старое описание",
            order_number=1,
            tags=["old"],
        )

        await sections_manager.update_section(
            section_id=created.id,
            name="Новое название",
            description="Новое описание",
            tags=["new", "updated"],
        )

        updated = await sections_manager.get_section_by_id(created.id)
        assert updated.name == "Новое название"
        assert updated.description == "Новое описание"
        assert updated.tags == ["new", "updated"]
        assert updated.order_number == 1  # не должно измениться

    async def test_updates_partial_fields(
        self,
        sections_manager,
        course_factory,
    ):
        course = await course_factory()
        created = await sections_manager.create_section(
            course_id=course.id,
            name="Имя",
            description="Описание",
            order_number=1,
            tags=["tag"],
        )

        await sections_manager.update_section(
            section_id=created.id,
            name="Новое имя",
            description="Описание",
            tags=["tag"],
        )

        updated = await sections_manager.get_section_by_id(created.id)
        assert updated.name == "Новое имя"
        assert updated.description == "Описание"

    async def test_can_update_description_to_longer_text(
            self,
            sections_manager,
            course_factory,
    ):
        course = await course_factory()
        created = await sections_manager.create_section(
            course_id=course.id,
            name="Раздел",
            description="Краткое описание",
            order_number=1,
            tags=[],
        )

        # Используем максимально допустимую длину (500 символов)
        long_description = "A" * 500
        await sections_manager.update_section(
            section_id=created.id,
            name="Раздел",
            description=long_description,
            tags=[],
        )

        updated = await sections_manager.get_section_by_id(created.id)
        assert updated.description == long_description

    async def test_cannot_update_description_too_long(
            self,
            sections_manager,
            course_factory,
    ):
        course = await course_factory()
        created = await sections_manager.create_section(
            course_id=course.id,
            name="Раздел",
            description="Описание",
            order_number=1,
            tags=[],
        )

        too_long_description = "A" * 501
        with pytest.raises(BadRequestError, match="Описание раздела не может превышать 500 символов!"):
            await sections_manager.update_section(
                section_id=created.id,
                name="Раздел",
                description=too_long_description,
                tags=[],
            )


class TestDeleteSection:
    async def test_deletes_section(
        self,
        sections_manager,
        course_factory,
    ):
        course = await course_factory()
        created = await sections_manager.create_section(
            course_id=course.id,
            name="Для удаления",
            description="",
            order_number=1,
            tags=[],
        )

        await sections_manager.delete_section(created.id)

        with pytest.raises(ObjectMissingError):
            await sections_manager.get_section_by_id(created.id)

    async def test_delete_nonexistent_section_does_not_raise(
        self,
        sections_manager,
    ):
        with pytest.raises(ObjectMissingError, match="Раздела с таким идентификатором не найдено!"):
            await sections_manager.delete_section(uuid.uuid4())


class TestSwapSections:
    async def test_swaps_order_numbers(
        self,
        sections_manager,
        course_factory,
    ):
        course = await course_factory()
        section1 = await sections_manager.create_section(
            course_id=course.id,
            name="Первый",
            description="",
            order_number=1,
            tags=[],
        )
        section2 = await sections_manager.create_section(
            course_id=course.id,
            name="Второй",
            description="",
            order_number=2,
            tags=[],
        )

        await sections_manager.swap_sections(section1.id, section2.id)

        sec1 = await sections_manager.get_section_by_id(section1.id)
        sec2 = await sections_manager.get_section_by_id(section2.id)

        assert sec1.order_number == 2
        assert sec2.order_number == 1

    async def test_swaps_multiple_times(
        self,
        sections_manager,
        course_factory,
    ):
        course = await course_factory()
        section1 = await sections_manager.create_section(
            course_id=course.id,
            name="Первый",
            description="",
            order_number=1,
            tags=[],
        )
        section2 = await sections_manager.create_section(
            course_id=course.id,
            name="Второй",
            description="",
            order_number=2,
            tags=[],
        )
        section3 = await sections_manager.create_section(
            course_id=course.id,
            name="Третий",
            description="",
            order_number=3,
            tags=[],
        )

        await sections_manager.swap_sections(section1.id, section3.id)

        sec1 = await sections_manager.get_section_by_id(section1.id)
        sec2 = await sections_manager.get_section_by_id(section2.id)
        sec3 = await sections_manager.get_section_by_id(section3.id)

        assert sec1.order_number == 3
        assert sec2.order_number == 2
        assert sec3.order_number == 1

    async def test_raises_error_when_sections_from_different_courses(
        self,
        sections_manager,
        course_factory,
    ):
        course1 = await course_factory(name="Курс 1")
        course2 = await course_factory(name="Курс 2")

        section1 = await sections_manager.create_section(
            course_id=course1.id,
            name="Раздел 1",
            description="",
            order_number=1,
            tags=[],
        )
        section2 = await sections_manager.create_section(
            course_id=course2.id,
            name="Раздел 2",
            description="",
            order_number=1,
            tags=[],
        )

        with pytest.raises(DifferentSourcesContentSwapError, match="Обменяться порядковыми номерами между "
                                                                   "разделами можно только в пределах одного курса!"):
            await sections_manager.swap_sections(section1.id, section2.id)

    async def test_raises_error_when_section_does_not_exist(
        self,
        sections_manager,
        course_factory,
    ):
        course = await course_factory()
        section = await sections_manager.create_section(
            course_id=course.id,
            name="Существующий раздел",
            description="",
            order_number=1,
            tags=[],
        )

        # При попытке обмена с несуществующим разделом будет ошибка
        with pytest.raises(AssertionError):
            await sections_manager.swap_sections(section.id, uuid.uuid4())
