"""Пакет для маршрутизации запросов в приложении"""
from fastapi import APIRouter

from server.app.api.students_routes import students_router
from server.app.api.auth_routes import auth_router
from server.app.api.courses_routes import courses_router
from server.app.api.sections_routes import sections_router
from server.app.api.topics_router import topics_router

app_router = APIRouter(
    prefix="/api/v1",
)

app_router.include_router(
    auth_router,
)
app_router.include_router(
    courses_router,
)
app_router.include_router(
    sections_router,
)
app_router.include_router(
    topics_router,
)
app_router.include_router(
    students_router
)
