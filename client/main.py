import os

import httpx
from fastapi import FastAPI, Response, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

STATIC_PATH = os.path.join(str(os.path.dirname(__file__)), "static")
client_app = FastAPI()

client_app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")

templates = Jinja2Templates(directory="templates")

SERVER_AUTH_URL = "http://localhost:8080/readme/v1/"


@client_app.get("/client_healthcheck")
async def healthcheck() -> Response:
    return Response(status_code=status.HTTP_200_OK)


@client_app.get("/")
async def main_page(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


@client_app.get("/course/{course_id}")
async def course_page(request: Request, course_id: int):
    return templates.TemplateResponse(request, "course.html", {
        "request": request,
        "course_id": course_id
    })


@client_app.post("/auth/login")
async def proxy_login(request: Request):
    try:
        body = await request.json()
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{SERVER_AUTH_URL}/auth/login", json=body)
            resp.raise_for_status()
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        print(f"Ошибка: {e}")
        return JSONResponse({"detail": f"Внутренняя ошибка сервера: {str(e)}"}, status_code=500)
