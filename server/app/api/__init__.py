"""Пакет для маршрутизации запросов в приложении"""
from fastapi import APIRouter

from server.app.api.auth_routes import auth_router


app_router = APIRouter(prefix="/readme/v1")

app_router.include_router(auth_router)