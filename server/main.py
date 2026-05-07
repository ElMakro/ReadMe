import uvicorn
from fastapi import FastAPI, Response, status

from fastapi.middleware.cors import CORSMiddleware

from server.app.api import app_router
from server.config.settings import settings

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"])
app.include_router(app_router)


def run():
    uvicorn.run(app="main:app", port=settings.uvicorn_settings.server_port, reload=True)


@app.get("/server_healthcheck")
async def healthcheck():
    return Response(status_code=status.HTTP_200_OK)
