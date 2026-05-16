import uuid

from fastapi import Depends
from sqlalchemy import select

from server.config.db_dependency import DBDependency
from server.database.models import Notes, Topics
from server.schemas.notes import NotesList


class NotesManager:
    def __init__(self, db: DBDependency = Depends(DBDependency)) -> None:
        self.db = db
        self.notes_model = Notes
        self.topics_model = Topics

    async def get_notes_for_user(self, user_id: uuid.UUID, offset: int, limit: int) -> NotesList:
        async with (self.db.db_session() as session):
            query = select(
                self.notes_model.id.label("id"),
                self.notes_model.name.label("name"),
                self.notes_model.content.label("content"),
                self.notes_model.topic_id.label("topic_id"),
                self.topics_model.name.label("topic_name"),
                           ).join(
                self.topics_model, self.notes_model.topic_id == self.topics_model.id
            ).where(self.notes_model.student_id == user_id
                    ).order_by(self.notes_model.updated_at
                               ).offset(offset
                                        ).limit(limit)
            result = await session.execute(query)
            notes = result.mappings().all()
            return NotesList.model_validate(notes)
