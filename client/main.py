import os

from fastapi import FastAPI
from fastapi import Response
from fastapi import status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

STATIC_PATH = os.path.join(str(os.path.dirname(__file__)), "static")
client_app = FastAPI()

client_app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")

templates = Jinja2Templates(directory="templates")


@client_app.get("/client_healthcheck")
async def healthcheck() -> Response:
    return Response(status_code=status.HTTP_200_OK)


@client_app.get("/")
async def main_page(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

@client_app.get("/course/{course_id}")
async def course_page(request: Request, course_id: int):
    # Пока можно игнорировать course_id, но передадим его в шаблон
    return templates.TemplateResponse(request, "course.html", {
        "request": request,
        "course_id": course_id
    })
