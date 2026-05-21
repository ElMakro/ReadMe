import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status

from server.app.api.v1.common_schemas import (
    NOTE_ALREADY_EXISTS_ERROR_TEXT,
    NOTE_FIELDS_MISMATCH_ERROR_TEXT,
    NOTE_NOT_FOUND_ERROR_TEXT,
    UNPROCESSABLE_ENTITY_ERROR_TEXT,
    PaginationParameters,
)
from server.app.api.v1.notes.exceptions import NoteAlreadyExistsError, NoteFieldsMismatchError, NoteNotFoundError
from server.app.api.v1.notes.notes import CreateNote, NoteById, NotesList, ShortNoteInfo, UpdateNote
from server.app.api.v1.notes.notes_service import NotesService
from server.app.api.v1.users.users import UserVerification
from server.app.common_dependencies.depends import get_auth_user

notes_router = APIRouter(
    prefix="/notes",
    tags=["Взаимодействие с заметками"],
)


@notes_router.get(
    path="/get-note-for-topic/{topic_id}",
    summary="Получить конспект к текущей теме",
    response_description="Получен сохранённый конспект",
    status_code=status.HTTP_200_OK,
    response_model=ShortNoteInfo,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Пользователь не произвёл вход",
        },
        status.HTTP_204_NO_CONTENT: {
            "description": "Конспект ранее не был сохранён",
        },
    }
)
async def get_note_for_topic(
    user: Annotated[UserVerification, Depends(
                get_auth_user,
        )],
    notes_service: NotesService = Depends(
            NotesService,
        ),
    topic_id: uuid.UUID = Path(
            ...,
            description="Уникальный идентификатор темы",
        ),
) -> ShortNoteInfo | Response:
    """
    Получить конспект пользователя к теме.
    """
    if (note := await notes_service.get_note_for_topic(user.id, topic_id)) is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return note


@notes_router.post(
    path="/create-note",
    summary="Сохранить конспект",
    response_description="Конспект успешно добавлен",
    status_code=status.HTTP_201_CREATED,
    response_model=NoteById,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Пользователь не произвёл вход",
        },
        status.HTTP_409_CONFLICT: {
            "description": NOTE_ALREADY_EXISTS_ERROR_TEXT,
        }
    }
)
async def create_note(
    create_params: CreateNote,
    user: Annotated[UserVerification, Depends(
                get_auth_user,
        )],
    notes_service: NotesService = Depends(
            NotesService,
        ),
) -> NoteById:
    try:
        return await notes_service.create_note(user.id, create_params)
    except NoteAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(
                error,
            ),
        )


@notes_router.put(
    path="/update-note",
    summary="Обновить конспект",
    response_description="Конспект успешно обновлён",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Пользователь не произвёл вход",
        },
        status.HTTP_409_CONFLICT: {
            "description": NOTE_FIELDS_MISMATCH_ERROR_TEXT,
        }
    }
)
async def update_note(
    update_params: UpdateNote,
    user: Annotated[UserVerification, Depends(
                get_auth_user,
        )],
    notes_service: NotesService = Depends(
            NotesService,
        ),
):
    try:
        return await notes_service.update_note(user.id, update_params)
    except NoteFieldsMismatchError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(
                error,
            ),
        )

@notes_router.delete(
    path="/delete-note/{note_id}",
    summary="Удалить конспект",
    response_description="Конспект успешно удалён",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Пользователь не произвёл вход",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": NOTE_NOT_FOUND_ERROR_TEXT,
        }
    }
)
async def delete_note(
    user: Annotated[UserVerification, Depends(
                get_auth_user,
        )],
    notes_service: NotesService = Depends(
            NotesService,
        ),
    note_id: uuid.UUID = Path(
            ...,
            description="Уникальный идентификатор конспекта",
        ),
):
    try:
        return await notes_service.delete_note(note_id=note_id, user_id=user.id)
    except NoteNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                error,
            )
        )


@notes_router.get(
    path="/my-notes",
    summary="Получить список конспектов пользователя",
    response_description="Конспекты пользователя найдены",
    status_code=status.HTTP_200_OK,
    response_model=NotesList,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Пользователь не произвёл вход",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
        },
    }
)
async def get_my_notes(
    user: Annotated[UserVerification, Depends(
            get_auth_user,
    )],
    pagination_parameters: PaginationParameters = Depends(),
    notes_service: NotesService = Depends(
        NotesService,
    ),
) -> NotesList:
    """
    Получить пагинированный список конспектов, которые имеет текущий пользователь.
    """
    return await notes_service.get_notes_for_user(
        user=user,
        page=pagination_parameters.page,
        size=pagination_parameters.records_per_page,
    )
