from fastapi import APIRouter

notes_router = APIRouter(
    prefix="/notes",
    tags=["Взаимодействие с заметками"],
)
