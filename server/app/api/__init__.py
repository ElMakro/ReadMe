"""Пакет для маршрутизации запросов в приложении"""
from fastapi import APIRouter, Response, status

from server.app.api.v1 import v1_router

api_router = APIRouter(
    prefix="/api",
)

api_router.include_router(
    v1_router,
)


@api_router.get(
    "/healthcheck",
    summary="Проверка работоспособности сервера",
)
async def healthcheck():
    return Response(
        status_code=status.HTTP_200_OK,
    )
