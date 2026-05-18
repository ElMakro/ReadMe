from fastapi import Depends

from server.app.api.v1.notes.notes_manager import NotesManager
from server.app.api.v1.notes.notes import NotesList
from server.app.api.v1.users.users import UserVerification


class NotesService:
    def __init__(
            self,
            manager: NotesManager = Depends(
                NotesManager,
            ),
    ) -> None:
        self.notes_manager = manager

    async def get_notes_for_user(self, user: UserVerification, page: int, size: int) -> NotesList:
        offset = (page - 1) * size
        limit = size
        return await self.notes_manager.get_notes_for_user(user.id, offset, limit)
