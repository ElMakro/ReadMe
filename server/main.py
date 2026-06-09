import uvicorn
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from server.app.api import api_router
from server.app.api.v1.exceptions_handlers import register_global_exception_handlers
from server.config.settings import settings

app = FastAPI(
    description="API для взаимодействия с информационной системой ReadMe",
    version="1.0.0",
    title="API информационной системы ReadMe",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
)
app.include_router(
    api_router,
)

register_global_exception_handlers(app)


def run():
    uvicorn.run(
        app="main:app",
        port=settings.uvicorn_settings.server_port,
        reload=True,
    )


@app.get(
    "/server_healthcheck",
)
async def healthcheck():
    return Response(
        status_code=status.HTTP_200_OK,
    )
