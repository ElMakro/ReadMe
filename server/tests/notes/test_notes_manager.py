import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from server.app.api.v1.notes.exceptions import (
    NoteAlreadyExistsError,
    NoteFieldsMismatchError,
    NoteNotFoundError,
)
from server.app.api.v1.notes.notes import NoteById, NotesList
from server.database.models import Notes

pytestmark = pytest.mark.asyncio


class TestGetNoteForTopic:
    async def test_returns_note_when_exists(self, notes_manager, student_factory, topic_factory):
        student = await student_factory()
        topic = await topic_factory()
        created = await notes_manager.create_note(student.id, topic.id, "My note", "Content")
        result = await notes_manager.get_note_for_topic(student.id, topic.id)
        assert result is not None
        assert result.id == created.id
        assert result.name == "My note"
        assert result.content == "Content"

    async def test_returns_none_if_not_exists(self, notes_manager, student_factory, topic_factory):
        student = await student_factory()
        topic = await topic_factory()
        result = await notes_manager.get_note_for_topic(student.id, topic.id)
        assert result is None


class TestCreateNote:
    async def test_creates_note_successfully(self, notes_manager, student_factory, topic_factory, db_engine):
        student = await student_factory()
        topic = await topic_factory()
        result = await notes_manager.create_note(student.id, topic.id, "New note", "Content here")
        assert isinstance(result, NoteById)
        assert result.id is not None

        async_session = async_sessionmaker(db_engine, expire_on_commit=False)
        async with async_session() as session:
            note = await session.get(Notes, result.id)
            assert note is not None
            assert note.name == "New note"
            assert note.content == "Content here"
            assert note.student_id == student.id
            assert note.topic_id == topic.id

    async def test_duplicate_note_raises_already_exists(self, notes_manager, student_factory, topic_factory):
        student = await student_factory()
        topic = await topic_factory()
        await notes_manager.create_note(student.id, topic.id, "Note", "Content")
        with pytest.raises(NoteAlreadyExistsError):
            await notes_manager.create_note(student.id, topic.id, "Note", "Content")


class TestUpdateNote:
    async def test_updates_note_successfully(self, notes_manager, student_factory, topic_factory):
        student = await student_factory()
        topic = await topic_factory()
        note = await notes_manager.create_note(student.id, topic.id, "Old name", "Old content")
        await notes_manager.update_note(note.id, student.id, topic.id, "New name", "New content")
        updated = await notes_manager.get_note_for_topic(student.id, topic.id)
        assert updated.name == "New name"
        assert updated.content == "New content"

    async def test_update_with_wrong_user_id_raises_mismatch(self, notes_manager, student_factory, topic_factory):
        student = await student_factory()
        other_student = await student_factory()
        topic = await topic_factory()
        note = await notes_manager.create_note(student.id, topic.id, "Name", "Content")
        with pytest.raises(NoteFieldsMismatchError):
            await notes_manager.update_note(note.id, other_student.id, topic.id, "New", "New")

    async def test_update_with_wrong_topic_id_raises_mismatch(self, notes_manager, student_factory, topic_factory):
        student = await student_factory()
        topic1 = await topic_factory()
        topic2 = await topic_factory()
        note = await notes_manager.create_note(student.id, topic1.id, "Name", "Content")
        with pytest.raises(NoteFieldsMismatchError):
            await notes_manager.update_note(note.id, student.id, topic2.id, "New", "New")


class TestDeleteNote:
    async def test_deletes_note_successfully(self, notes_manager, student_factory, topic_factory):
        student = await student_factory()
        topic = await topic_factory()
        note = await notes_manager.create_note(student.id, topic.id, "To delete", "Content")
        await notes_manager.delete_note(note.id, student.id)
        result = await notes_manager.get_note_for_topic(student.id, topic.id)
        assert result is None

    async def test_delete_nonexistent_note_raises_not_found(self, notes_manager, student_factory):
        student = await student_factory()
        with pytest.raises(NoteNotFoundError):
            await notes_manager.delete_note(uuid.uuid4(), student.id)


class TestGetNotesForUser:
    async def test_returns_notes_list_with_pagination(self, notes_manager, student_factory, topic_factory):
        student = await student_factory()
        topic1 = await topic_factory(name="Topic A")
        topic2 = await topic_factory(name="Topic B")
        await notes_manager.create_note(student.id, topic1.id, "Note1", "Short content")
        await notes_manager.create_note(student.id, topic2.id, "Note2", "Another content")
        result = await notes_manager.get_notes_for_user(student.id, offset=0, limit=10)
        assert isinstance(result, NotesList)
        assert len(result.root) == 2
        contents = {note.content for note in result.root}
        assert contents == {"Short content", "Another content"}
        topic_names = {note.topic_name for note in result.root}
        assert topic_names == {"Topic A", "Topic B"}

    async def test_returns_empty_list_when_no_notes(self, notes_manager, student_factory):
        student = await student_factory()
        result = await notes_manager.get_notes_for_user(student.id, offset=0, limit=10)
        assert result.root == []

    async def test_pagination_offset_and_limit(self, notes_manager, student_factory, topic_factory):
        student = await student_factory()
        topics = [await topic_factory(name=f"Topic{i}") for i in range(5)]
        for topic in topics:
            await notes_manager.create_note(student.id, topic.id, f"Note on {topic.name}", "Content")
        page1 = await notes_manager.get_notes_for_user(student.id, offset=0, limit=2)
        page2 = await notes_manager.get_notes_for_user(student.id, offset=2, limit=2)
        assert len(page1.root) == 2
        assert len(page2.root) == 2
        ids1 = {note.id for note in page1.root}
        ids2 = {note.id for note in page2.root}
        assert ids1.isdisjoint(ids2)

    async def test_notes_ordered_by_updated_at_desc(self, notes_manager, student_factory, topic_factory):
        student = await student_factory()
        topic1 = await topic_factory(name="First topic")
        topic2 = await topic_factory(name="Second topic")
        note1 = await notes_manager.create_note(student.id, topic1.id, "First", "Content")
        note2 = await notes_manager.create_note(student.id, topic2.id, "Second", "Other content")
        await notes_manager.update_note(note1.id, student.id, topic1.id, "First updated", "New content")
        result = await notes_manager.get_notes_for_user(student.id, offset=0, limit=10)
        assert len(result.root) == 2
        assert result.root[0].id == note1.id
        assert result.root[1].id == note2.id
