import os
from uuid import UUID

import httpx
from fastapi import FastAPI, Response, status, Query
from fastapi.requests import Request
from fastapi.responses import JSONResponse,  RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from math import ceil


STATIC_PATH = os.path.join(str(os.path.dirname(__file__)), "static")
client_app = FastAPI()

client_app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")

templates = Jinja2Templates(directory="templates")

SERVER_URL = "http://localhost:8080/readme/v1/"

ALL_COURSES = []
for i in range(1, 41):
    ALL_COURSES.append({
        "id": i,
        "title": f"Курс {i}",
        "instructor": f"Преподаватель {i}",
        "description": f"Описание курса {i} – подробное руководство для начинающих."
    })


def search_courses(query: str, courses: list) -> list:
    if not query:
        return courses
    q = query.lower()
    return [
        c for c in courses
        if q in c["title"].lower()
        or q in c["instructor"].lower()
        or q in c["description"].lower()
    ]


@client_app.get("/client_healthcheck")
async def healthcheck() -> Response:
    return Response(status_code=status.HTTP_200_OK)


@client_app.get("/")
async def main_page(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


@client_app.get("/courses")
async def get_courses(
    page: int = Query(1, ge=1),
    limit: int = Query(8, ge=1, le=100),
    search: str = Query("", max_length=200)
):
    filtered = search_courses(search, ALL_COURSES)
    total = len(filtered)
    total_pages = ceil(total / limit) if total else 1

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * limit
    end = start + limit
    page_courses = filtered[start:end]

    return {
        "courses": page_courses,
        "page": page,
        "total_pages": total_pages,
        "total_items": total
    }


@client_app.get("/course/{course_id}")
async def course_page(request: Request, course_id: int):
    course = next((c for c in ALL_COURSES if c["id"] == course_id), None)
    course_title = course["title"] if course else f"Курс {course_id}"

    return templates.TemplateResponse(request, "course.html", {
        "request": request,
        "course_id": course_id,
        "course_title": course_title
    })


@client_app.post("/auth/login")
async def proxy_login(request: Request):
    try:
        body = await request.json()
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{SERVER_URL}/auth/login", json=body)
            resp.raise_for_status()
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        print(f"Ошибка: {e}")
        return JSONResponse({"detail": f"Внутренняя ошибка сервера: {str(e)}"}, status_code=500)


@client_app.post("/auth/reg")
async def proxy_reg(request: Request):
    try:
        body = await request.json()
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{SERVER_URL}/auth/reg", json=body)
            resp.raise_for_status()
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        print(f"Ошибка: {e}")
        return JSONResponse({"detail": f"Внутренняя ошибка сервера: {str(e)}"}, status_code=500)


@client_app.get("/me")
async def profile_redirect(request: Request):
    """
    Проксируем запрос к бэкенду, передавая куки браузера.
    Если получен текущий пользователь — редиректим на /me/{id}.
    Иначе показываем страницу профиля с заглушкой и ошибкой.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SERVER_URL}/me",
                cookies=request.cookies
            )
            resp.raise_for_status()
            user_data = resp.json()
            user_id = user_data.get("id") or user_data.get("nickname")
            if user_id:
                return RedirectResponse(f"/me/{user_id}")
            else:
                # Бэкенд вернул пустой ответ
                return templates.TemplateResponse(request, "profile.html", {
                    "request": request,
                    "user": {
                        "nickname": "unknown",
                        "email": "",
                        "photo_url": "https://via.placeholder.com/150"
                    },
                    "error": "Не удалось определить пользователя"
                })
    except Exception as e:
        print(f"Ошибка получения текущего пользователя: {e}")
        # Бэкенд недоступен или ошибка — показываем профиль с заглушкой
        return templates.TemplateResponse(request, "profile.html", {
            "request": request,
            "user": {
                "nickname": "",
                "email": "",
                "photo_url": "https://via.placeholder.com/150"
            },
            "error": "Сервер временно недоступен. Попробуйте позже."
        })

@client_app.get("/me/{id}")
async def profile(request: Request, id: str):
    # пробуем как UUID, потом как никнейм, иначе заглушка
    try:
        UUID(id)
        is_uuid = True
    except ValueError:
        is_uuid = False

    try:
        if is_uuid:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{SERVER_URL}/me/{id}")
                resp.raise_for_status()
                user_data = resp.json()
        else:
            # Запрос профиля по никнейму (если есть такой эндпоинт)
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{SERVER_URL}/users/nickname/{id}")
                resp.raise_for_status()
                user_data = resp.json()
    except Exception as e:
        print(f"Ошибка получения профиля: {e}")
        # Заглушка, пока сервер не реализован
        user_data = {
            "nickname": id,
            "email": f"{id}@example.com",
            "photo_url": "https://via.placeholder.com/150"
        }

    return templates.TemplateResponse(request, "profile.html", {
        "request": request,
        "user": user_data
    })
