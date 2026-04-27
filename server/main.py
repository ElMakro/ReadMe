import uvicorn
from fastapi import FastAPI, Response, status

from config.settings import settings
from server.app.api import app_router

app = FastAPI()
app.include_router(app_router)


def run():
    uvicorn.run(app="main:app", port=settings.uvicorn_settings.server_port, reload=True)


@app.get("/server_healthcheck")
async def healthcheck():
    return Response(status_code=status.HTTP_200_OK)
