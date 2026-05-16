from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from server.app.service.depends import get_current_user
from server.app.service.notes_service import NotesService
from server.schemas.common import UNPROCESSABLE_ENTITY_ERROR_TEXT
from server.schemas.notes import NotesList
from server.schemas.users import UserVerification

notes_router = APIRouter(
    prefix="/notes",
    tags=["Взаимодействие с заметками"],
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
            get_current_user,
    )],
    page: int = Query(1, ge=1),
    records_per_page: int = Query(10, ge=1, le=20),
    notes_service: NotesService = Depends(
        NotesService,
    ),
) -> NotesList:
    """
    Получить пагинированный список конспектов, которые имеет текущий пользователь.
    """
    return await notes_service.get_notes_for_user(
        user=user,
        page=page,
        size=records_per_page,
    )
