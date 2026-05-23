"""Пакет для первой версии API информационной системы ReadMe"""
from fastapi import APIRouter

from server.app.api.v1.auth.auth_routes import auth_router
from server.app.api.v1.content.content_routes import content_router
from server.app.api.v1.courses.courses_routes import courses_router
from server.app.api.v1.notes.notes_routes import notes_router
from server.app.api.v1.sections.sections_routes import sections_router
from server.app.api.v1.topics.topics_router import topics_router
from server.app.api.v1.users.users_routes import users_router

v1_router = APIRouter(
    prefix="/v1",
)

v1_router.include_router(
    auth_router,
)
v1_router.include_router(
    courses_router,
)
v1_router.include_router(
    sections_router,
)
v1_router.include_router(
    topics_router,
)
v1_router.include_router(
    users_router,
)
v1_router.include_router(
    notes_router,
)
v1_router.include_router(
    content_router,
)
