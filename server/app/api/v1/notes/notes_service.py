import uuid

from fastapi import Depends

from server.app.api.v1.notes.notes import CreateNote, NoteById, NotesList, ShortNoteInfo, UpdateNote
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

    async def create_note(self, user_id: uuid.UUID, create_params: CreateNote) -> NoteById:
        return await self.notes_manager.create_note(
            user_id,
            create_params.topic_id,
            create_params.name,
            create_params.content
        )

    async def update_note(self, user_id: uuid.UUID, update_params: UpdateNote) -> None:
        return await self.notes_manager.update_note(
            note_id=update_params.note_id,
            user_id=user_id,
            topic_id=update_params.topic_id,
            name=update_params.name,
            content=update_params.content,
        )

    async def delete_note(self, note_id: uuid.UUID, user_id: uuid.UUID):
        return await self.notes_manager.delete_note(
            note_id=note_id,
            user_id=user_id,
        )

    async def get_notes_for_user(self, user: UserVerification, page: int, size: int) -> NotesList:
        offset = (page - 1) * size
        limit = size
        return await self.notes_manager.get_notes_for_user(user.id, offset, limit)
