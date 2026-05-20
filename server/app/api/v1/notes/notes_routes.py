from typing import Annotated

from fastapi import APIRouter, Depends, status

from server.app.api.v1.common_schemas import UNPROCESSABLE_ENTITY_ERROR_TEXT, PaginationParameters
from server.app.api.v1.notes.notes import NotesList
from server.app.api.v1.notes.notes_service import NotesService
from server.app.api.v1.users.users import UserVerification
from server.app.common_dependencies.depends import get_auth_user

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
