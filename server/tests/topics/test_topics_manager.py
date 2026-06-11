import uuid

import pytest

from server.app.api.v1.exceptions import ObjectMissingError
from server.app.api.v1.topics.topics import TopicContent, TopicContentBlock

pytestmark = pytest.mark.asyncio


class TestCreateTopic:
    async def test_creates_topic_and_returns_id(
        self,
        topics_manager,
        topic_factory,
    ):
        topic = await topic_factory(name="Новая тема", tags=["python", "basics"])

        assert topic.id is not None

        fetched = await topics_manager.get_topic_by_id(topic.id)
        assert fetched.name == "Новая тема"
        assert fetched.tags == ["python", "basics"]

    async def test_creates_topic_with_empty_tags(
        self,
        topics_manager,
        topic_factory,
    ):
        topic = await topic_factory(name="Без тегов", tags=[])

        fetched = await topics_manager.get_topic_by_id(topic.id)
        assert fetched.tags == []

    async def test_creates_topic_with_custom_order_number(
        self,
        topics_manager,
        section_factory,
        topic_factory,
    ):
        section = await section_factory()
        topic = await topic_factory(
            section_id=section.id,
            name="Тема с номером 10",
            order_number=10,
        )

        assert topic.order_number == 10

    async def test_creates_topic_with_auto_order_number(
        self,
        topics_manager,
        section_factory,
        topic_factory,
    ):
        section = await section_factory()
        topic1 = await topic_factory(section_id=section.id, order_number=1)
        topic2 = await topic_factory(section_id=section.id)  # auto
        topic3 = await topic_factory(section_id=section.id)  # auto

        assert topic1.order_number == 1
        assert topic2.order_number == 2
        assert topic3.order_number == 3


class TestGetTopicById:
    async def test_returns_topic_when_exists(
        self,
        topics_manager,
        topic_factory,
    ):
        created = await topic_factory(name="Тестовая тема")

        topic = await topics_manager.get_topic_by_id(created.id)

        assert topic.id == created.id
        assert topic.name == "Тестовая тема"

    async def test_raises_error_when_not_found(
        self,
        topics_manager,
    ):
        with pytest.raises(ObjectMissingError, match="Темы с таким id не существует!"):
            await topics_manager.get_topic_by_id(uuid.uuid4())


class TestCheckSectionHaveTopicWithOrderNumber:
    async def test_returns_false_when_no_topic(
        self,
        topics_manager,
        section_factory,
    ):
        section = await section_factory()

        result = await topics_manager.check_section_have_topic_with_order_number(
            section.id, 999
        )
        assert result is False

    async def test_returns_true_when_topic_exists(
        self,
        topics_manager,
        topic_factory,
    ):
        topic = await topic_factory(order_number=5)

        result = await topics_manager.check_section_have_topic_with_order_number(
            topic.section_id, 5
        )
        assert result is True


class TestGetTopicsBySectionId:
    async def test_returns_topics_ordered_by_order_number(
        self,
        topics_manager,
        section_factory,
        topic_factory,
    ):
        section = await section_factory()

        await topic_factory(section_id=section.id, order_number=3, name="Тема 3")
        await topic_factory(section_id=section.id, order_number=1, name="Тема 1")
        await topic_factory(section_id=section.id, order_number=2, name="Тема 2")

        result = await topics_manager.get_topics_by_section_id(section.id)

        assert len(result.root) == 3
        names = [t.name for t in result.root]
        assert names == ["Тема 1", "Тема 2", "Тема 3"]

    async def test_returns_empty_list_for_section_without_topics(
        self,
        topics_manager,
        section_factory,
    ):
        section = await section_factory()

        result = await topics_manager.get_topics_by_section_id(section.id)
        assert result.root == []


class TestGetTopicsByCourseId:
    async def test_returns_all_topics_from_course(
        self,
        topics_manager,
        course_factory,
        section_factory,
        topic_factory,
    ):
        course = await course_factory()
        section1 = await section_factory(course_id=course.id)
        section2 = await section_factory(course_id=course.id)

        await topic_factory(section_id=section1.id, name="Тема из раздела 1")
        await topic_factory(section_id=section2.id, name="Тема из раздела 2")

        result = await topics_manager.get_topics_by_course_id(course.id)

        assert len(result.root) == 2
        names = [t.name for t in result.root]
        assert "Тема из раздела 1" in names
        assert "Тема из раздела 2" in names


class TestUpdateTopic:
    async def test_updates_all_fields(
        self,
        topics_manager,
        topic_factory,
    ):
        created = await topic_factory(name="Старое название", tags=["old"])

        await topics_manager.update_topic(
            topic_id=created.id,
            name="Новое название",
            tags=["new", "updated"],
            raw_content=TopicContent(root=[
                TopicContentBlock(type="markdown", content=["# Новый контент"])
            ]),
            rendered_content=TopicContent(root=[
                TopicContentBlock(type="markdown", content=["<h1>Новый контент</h1>"])
            ]),
        )

        updated = await topics_manager.get_topic_by_id(created.id)
        assert updated.name == "Новое название"
        assert updated.tags == ["new", "updated"]

    async def test_updates_only_name(
        self,
        topics_manager,
        topic_factory,
    ):
        created = await topic_factory(name="Старое имя", tags=["old"])

        await topics_manager.update_topic(
            topic_id=created.id,
            name="Новое имя",
            tags=["old"],
            raw_content=TopicContent(root=[
                TopicContentBlock(type="markdown", content=["# Контент"])
            ]),
            rendered_content=TopicContent(root=[
                TopicContentBlock(type="markdown", content=["<h1>Контент</h1>"])
            ]),
        )

        updated = await topics_manager.get_topic_by_id(created.id)
        assert updated.name == "Новое имя"
        assert updated.tags == ["old"]


class TestDeleteTopic:
    async def test_deletes_topic(
        self,
        topics_manager,
        topic_factory,
    ):
        created = await topic_factory()

        await topics_manager.delete_topic(created.id)

        with pytest.raises(ObjectMissingError):
            await topics_manager.get_topic_by_id(created.id)

    async def test_delete_nonexistent_topic_raises_error(
        self,
        topics_manager,
    ):
        with pytest.raises(ObjectMissingError, match="Тема с таким ID не найдена!"):
            await topics_manager.delete_topic(uuid.uuid4())


class TestGetAndBlockTopic:
    async def test_returns_topic_and_session(
        self,
        topics_manager,
        topic_factory,
    ):
        created = await topic_factory()

        topic, topic_response, session = await topics_manager.get_and_block_topic(created.id)

        assert topic.id == created.id
        assert topic_response.id == created.id
        assert session is not None
        await session.close()

    async def test_raises_error_when_not_found(
        self,
        topics_manager,
    ):
        with pytest.raises(ObjectMissingError, match="Темы с таким id не существует!"):
            await topics_manager.get_and_block_topic(uuid.uuid4())


class TestChangeTopicContentAndUnblock:
    async def test_updates_content_and_closes_session(
        self,
        topics_manager,
        topic_factory,
    ):
        created = await topic_factory()
        new_content = TopicContent(root=[
            TopicContentBlock(type="markdown", content=["# Обновлённый контент"])
        ])

        topic, _, session = await topics_manager.get_and_block_topic(created.id)

        await topics_manager.change_topic_content_and_unblock(new_content, topic, session)

        updated = await topics_manager.get_topic_by_id(created.id)
        assert updated.raw_content.root[0].type == "markdown"
        assert updated.raw_content.root[0].content == ["# Обновлённый контент"]
