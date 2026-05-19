import uuid

from fastapi import Depends
from sqlalchemy import desc, func, select

from server.app.api.v1.notes.notes import NotesList, ShortNoteInfo
from server.config.db_dependency import DBDependency
from server.database.models import Notes, Topics


class NotesManager:
    def __init__(self, db: DBDependency = Depends(DBDependency)) -> None:
        self.db = db
        self.notes_model = Notes
        self.topics_model = Topics

    async def get_note_for_topic(self, user_id: uuid.UUID, topic_id: uuid.UUID) -> ShortNoteInfo | None:
        async with self.db.db_session() as session:
            query = select(
                self.notes_model.id,
                self.notes_model.name,
                self.notes_model.content,
            ).filter_by(
                student_id=user_id,
                topic_id=topic_id
            )
            if (note := (await session.execute(query)).one_or_none()) is None:
                return None
            return ShortNoteInfo.model_validate(note)

    async def get_notes_for_user(self, user_id: uuid.UUID, offset: int, limit: int) -> NotesList:
        async with (self.db.db_session() as session):
            query = select(
                self.notes_model.id.label("id"),
                self.notes_model.name.label("name"),
                func.substring(self.notes_model.content, 1, 50).label("content"),
                self.notes_model.topic_id.label("topic_id"),
                self.topics_model.name.label("topic_name"),
                           ).join(
                self.topics_model, self.notes_model.topic_id == self.topics_model.id
            ).where(self.notes_model.student_id == user_id
                    ).order_by(
                desc(self.notes_model.updated_at)
                               ).offset(offset
                                        ).limit(limit)
            result = await session.execute(query)
            notes = result.mappings().all()
            return NotesList.model_validate(notes)
