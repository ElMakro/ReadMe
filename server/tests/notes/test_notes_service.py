import uuid
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from server.app.api.v1.notes.notes import CreateNote, NoteById, NoteInfo, NotesList, ShortNoteInfo, UpdateNote
from server.app.api.v1.notes.notes_service import NotesService
from server.app.api.v1.users.users import UserVerification
from server.enums.role import Role

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_notes_manager(mocker: MockerFixture):
    manager = mocker.AsyncMock()
    manager.get_note_for_topic = mocker.AsyncMock()
    manager.create_note = mocker.AsyncMock()
    manager.update_note = mocker.AsyncMock()
    manager.delete_note = mocker.AsyncMock()
    manager.get_notes_for_user = mocker.AsyncMock()
    return manager


@pytest.fixture
def notes_service(mock_notes_manager):
    return NotesService(manager=mock_notes_manager)


class TestGetNoteForTopic:
    async def test_returns_note_when_exists(self, notes_service, mock_notes_manager):
        user_id = uuid.uuid4()
        topic_id = uuid.uuid4()
        expected_note = MagicMock(spec=ShortNoteInfo)
        mock_notes_manager.get_note_for_topic.return_value = expected_note

        result = await notes_service.get_note_for_topic(user_id, topic_id)

        mock_notes_manager.get_note_for_topic.assert_awaited_once_with(user_id, topic_id)
        assert result == expected_note

    async def test_returns_none_when_not_found(self, notes_service, mock_notes_manager):
        user_id = uuid.uuid4()
        topic_id = uuid.uuid4()
        mock_notes_manager.get_note_for_topic.return_value = None

        result = await notes_service.get_note_for_topic(user_id, topic_id)

        mock_notes_manager.get_note_for_topic.assert_awaited_once_with(user_id, topic_id)
        assert result is None


class TestCreateNote:
    async def test_creates_note_and_returns_id(self, notes_service, mock_notes_manager):
        user_id = uuid.uuid4()
        create_params = CreateNote(topic_id=uuid.uuid4(), name="Test Note", content="Content")
        expected_note = NoteById(id=uuid.uuid4())
        mock_notes_manager.create_note.return_value = expected_note

        result = await notes_service.create_note(user_id, create_params)

        mock_notes_manager.create_note.assert_awaited_once_with(
            user_id,
            create_params.topic_id,
            create_params.name,
            create_params.content
        )
        assert result == expected_note


class TestUpdateNote:
    async def test_updates_note(self, notes_service, mock_notes_manager):
        user_id = uuid.uuid4()
        update_params = UpdateNote(
            note_id=uuid.uuid4(),
            topic_id=uuid.uuid4(),
            name="Updated Name",
            content="Updated Content"
        )
        mock_notes_manager.update_note.return_value = None

        await notes_service.update_note(user_id, update_params)

        mock_notes_manager.update_note.assert_awaited_once_with(
            note_id=update_params.note_id,
            user_id=user_id,
            topic_id=update_params.topic_id,
            name=update_params.name,
            content=update_params.content,
        )


class TestDeleteNote:
    async def test_deletes_note(self, notes_service, mock_notes_manager):
        note_id = uuid.uuid4()
        user_id = uuid.uuid4()

        await notes_service.delete_note(note_id, user_id)

        mock_notes_manager.delete_note.assert_awaited_once_with(
            note_id=note_id,
            user_id=user_id,
        )


class TestGetNotesForUser:
    async def test_returns_notes_list_with_pagination(self, notes_service, mock_notes_manager):
        from server.app.api.v1.notes.notes import NotesList
        from server.enums.role import Role

        user = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.STUDENT, session_id="sess123")
        page = 2
        size = 10

        note1 = NoteInfo(
            id=uuid.uuid4(),
            name="Note 1",
            content="Content 1",
            topic_id=uuid.uuid4(),
            topic_name="Topic 1"
        )
        note2 = NoteInfo(
            id=uuid.uuid4(),
            name="Note 2",
            content="Content 2",
            topic_id=uuid.uuid4(),
            topic_name="Topic 2"
        )
        expected_notes = NotesList(root=[note1, note2])
        mock_notes_manager.get_notes_for_user.return_value = expected_notes

        result = await notes_service.get_notes_for_user(user, page, size)

        mock_notes_manager.get_notes_for_user.assert_awaited_once_with(
            user.id, 10, 10
        )
        assert result == expected_notes

    @pytest.mark.parametrize("page,size,expected_offset,expected_limit", [
        (1, 5, 0, 5),
        (3, 20, 40, 20),
    ])
    async def test_pagination_calculates_offset_correctly(
        self, notes_service, mock_notes_manager, page, size, expected_offset, expected_limit
    ):
        user = UserVerification(id=uuid.uuid4(), nickname="user", role=Role.STUDENT, session_id="sess123")
        mock_notes_manager.get_notes_for_user.return_value = NotesList(root=[])

        await notes_service.get_notes_for_user(user, page, size)

        mock_notes_manager.get_notes_for_user.assert_awaited_once_with(
            user.id, expected_offset, expected_limit
        )
