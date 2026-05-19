import uuid

from fastapi import Depends

from server.app.api.v1.notes.notes import NotesList, ShortNoteInfo
from server.app.api.v1.notes.notes_manager import NotesManager
from server.app.api.v1.users.users import UserVerification


class NotesService:
    def __init__(
            self,
            manager: NotesManager = Depends(
                NotesManager,
            ),
    ) -> None:
        self.notes_manager = manager

    async def get_note_for_topic(self, user_id: uuid.UUID, topic_id: uuid.UUID) -> ShortNoteInfo | None:
        return await self.notes_manager.get_note_for_topic(user_id, topic_id)

    async def get_notes_for_user(self, user: UserVerification, page: int, size: int) -> NotesList:
        offset = (page - 1) * size
        limit = size
        return await self.notes_manager.get_notes_for_user(user.id, offset, limit)
