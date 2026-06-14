import uuid

from fastapi import Depends
from sqlalchemy import delete, desc, func, insert, select, update
from sqlalchemy.exc import IntegrityError

from server.app.api.v1.common_schemas import (
    NOTE_ALREADY_EXISTS_ERROR_TEXT,
    NOTE_FIELDS_MISMATCH_ERROR_TEXT,
    NOTE_NOT_FOUND_ERROR_TEXT, TOPIC_NOT_FOUND_ERROR_TEXT,
)
from server.app.api.v1.notes.exceptions import NoteAlreadyExistsError, NoteFieldsMismatchError, NoteNotFoundError, \
    TopicNotFoundError
from server.app.api.v1.notes.notes import NoteById, NotesList, ShortNoteInfo
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

    async def update_note(self, note_id: uuid.UUID, user_id: uuid.UUID, topic_id: uuid.UUID, name: str, content: str) \
            -> None:
        async with self.db.db_session() as session:
            query = update(
                self.notes_model
            ).where(
                self.notes_model.id == note_id,
                self.notes_model.student_id == user_id,
                self.notes_model.topic_id == topic_id,
            ).values(
                name=name,
                content=content,
            ).returning(
                self.notes_model.id,
            )
            if (await session.execute(query)).scalar_one_or_none() is None:
                raise NoteFieldsMismatchError(NOTE_FIELDS_MISMATCH_ERROR_TEXT)
            await session.commit()
            return

    async def create_note(self, user_id: uuid.UUID, topic_id: uuid.UUID, name: str, content: str) -> NoteById:
        async with self.db.db_session() as session:
            topic_exists_query = select(self.topics_model.id).where(self.topics_model.id == topic_id)
            topic_exists = await session.execute(topic_exists_query)
            if topic_exists.scalar_one_or_none() is None:
                raise TopicNotFoundError(TOPIC_NOT_FOUND_ERROR_TEXT)

            query = insert(
                self.notes_model
            ).values(
                student_id=user_id,
                topic_id=topic_id,
                name=name,
                content=content,
            ).returning(self.notes_model.id)
            try:
                result = await session.execute(query)
            except IntegrityError:
                raise NoteAlreadyExistsError(NOTE_ALREADY_EXISTS_ERROR_TEXT)
            await session.commit()
            data = result.scalar_one()
            return NoteById(id=data)

    async def delete_note(self, note_id: uuid.UUID, user_id: uuid.UUID) -> None:
        async with self.db.db_session() as session:
            query = delete(
                self.notes_model
            ).where(
                self.notes_model.id == note_id,
                self.notes_model.student_id == user_id,
            )
            result = await session.execute(query)
            await session.commit()
            if not result.rowcount:
                raise NoteNotFoundError(NOTE_NOT_FOUND_ERROR_TEXT)
            return

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
