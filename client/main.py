import os

import httpx
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

STATIC_PATH = os.path.join(os.path.dirname(__file__), "static")
client_app = FastAPI()
client_app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")
templates = Jinja2Templates(directory="templates")

# Реальный адрес бэкенда
BACKEND_URL = "http://localhost:8080/api/v1/"

# Добавьте эту функцию после импортов
async def get_course_title(course_id: str, cookies: dict) -> str:
    """Возвращает название курса по его ID, или None при ошибке."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{BACKEND_URL}courses/{course_id}",
                cookies=cookies,
                timeout=5.0
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("name")
        except Exception:
            pass
    return None

# ========== СТРАНИЦЫ ==========

@client_app.get("/client_healthcheck")
async def healthcheck() -> Response:
    return Response(status_code=status.HTTP_200_OK)

@client_app.get("/")
async def main_page(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "request": request,
        "api_base_url": BACKEND_URL
    })

@client_app.get("/course/{course_id}")
async def course_page(request: Request, course_id: str):  # course_id теперь UUID
    # Можно заранее получить данные курса через бэкенд
    return templates.TemplateResponse(request, "course.html", {
        "request": request,
        "course_id": course_id,
        "api_base_url": BACKEND_URL
    })


@client_app.get("/me")
async def profile_redirect(request: Request):
    # Просто отдаём шаблон, данные загрузит JS через /users/profile
    return templates.TemplateResponse(request, "profile.html", {
        "request": request,
        "user": None,          # важно: шаблон должен быть готов к None
        "api_base_url": BACKEND_URL
    })

@client_app.get("/me/{user_id}")
async def profile(request: Request, user_id: str):
    # Также просто отдаём страницу. ID может пригодиться для JS, но пока не используем.
    return templates.TemplateResponse(request, "profile.html", {
        "request": request,
        "user": {"id": user_id},  # минимальные данные, чтобы шаблон не упал
        "api_base_url": BACKEND_URL
    })

@client_app.get("/my-courses")
async def my_courses_page(request: Request):
    return templates.TemplateResponse(request, "my_courses.html", {
        "request": request,
        "api_base_url": BACKEND_URL
    })

@client_app.get("/created-courses")
async def created_courses_page(request: Request):
    return templates.TemplateResponse(request, "created_courses.html", {
        "request": request,
        "api_base_url": BACKEND_URL
    })

@client_app.get("/create-course")
async def create_course_form(request: Request):
    return templates.TemplateResponse(request, "course_creation/create_course.html", {
        "request": request,
        "api_base_url": BACKEND_URL
    })

@client_app.get("/course/{course_id}/sections")
async def edit_sections(request: Request, course_id: str):
    course_title = await get_course_title(course_id, request.cookies)
    return templates.TemplateResponse(request, "course_creation/edit_sections.html", {
        "request": request,
        "course_id": course_id,
        "course_title": course_title,
        "api_base_url": BACKEND_URL
    })

@client_app.get("/course/{course_id}/section/{section_id}/topics")
async def edit_topics(request: Request, course_id: str, section_id: str):
    return templates.TemplateResponse(request, "course_creation/edit_topics.html", {
        "request": request,
        "course_id": course_id,
        "section_id": section_id,
        "api_base_url": BACKEND_URL
    })

@client_app.get("/course/{course_id}/section/{section_id}/topic/{topic_id}/blocks")
async def edit_blocks(request: Request, course_id: str, section_id: str, topic_id: str):
    return templates.TemplateResponse(request, "course_creation/edit_blocks.html", {
        "request": request,
        "course_id": course_id,
        "section_id": section_id,
        "topic_id": topic_id,
        "api_base_url": BACKEND_URL
    })

@client_app.get("/course/{course_id}/edit")
async def edit_course_page(request: Request, course_id: str):
    """Страница редактирования курса (использует ту же форму, что и создание)"""
    return templates.TemplateResponse(request, "course_creation/create_course.html", {
        "request": request,
        "course_id": course_id,
        "mode": "edit",
        "api_base_url": BACKEND_URL
    })


# ========== ПРОКСИ ДЛЯ API ==========

# Авторизация
@client_app.post("/auth/login")
@client_app.post("/auth/reg")
async def auth_proxy(request: Request):
    """Прокси для /auth/login и /auth/reg"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BACKEND_URL}{request.url.path}", json=body)
        # Передаём куки от бэкенда (если есть)
        response = JSONResponse(content=resp.json(), status_code=resp.status_code)
        if 'set-cookie' in resp.headers:
            response.headers['Set-Cookie'] = resp.headers['set-cookie']
        return response

@client_app.get("/auth/logout")
async def logout_proxy(request: Request):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}auth/logout", cookies=request.cookies)
        response = JSONResponse(content=resp.json(), status_code=resp.status_code)
        if 'set-cookie' in resp.headers:
            response.headers['Set-Cookie'] = resp.headers['set-cookie']
        return response

# Профиль
@client_app.get("/users/profile")
async def profile_proxy(request: Request):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}users/profile", cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Курсы (поиск)
@client_app.get("/courses/search")
async def search_courses_proxy(
    request: Request,
    course_name_prefix: str = "",
    page: int = 1,
    records_per_page: int = 10
):
    params = {
        "course_name_prefix": course_name_prefix,
        "page": page,
        "records_per_page": records_per_page
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BACKEND_URL}courses/search",
            params=params,
            cookies=request.cookies
        )
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

@client_app.get("/courses/authorized-search")
async def authorized_search_courses_proxy(
    request: Request,
    course_name_prefix: str = "",
    page: int = 1,
    records_per_page: int = 10
):
    params = {
        "page": page,
        "records_per_page": records_per_page
    }
    if course_name_prefix:
        params["course_name_prefix"] = course_name_prefix
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BACKEND_URL}courses/authorized-search",
            params=params,
            cookies=request.cookies
        )
        # Проксируем ответ как есть (бэкенд вернёт 401, если нет авторизации)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Мои курсы (на которые подписан)
@client_app.get("/courses/followed")
async def followed_courses_proxy(request: Request, page: int = 1, records_per_page: int = 10):
    params = {"page": page, "records_per_page": records_per_page}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}courses/followed-courses", params=params, cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Курсы, где я преподаватель
@client_app.get("/courses/controlled")
async def controlled_courses_proxy(request: Request, page: int = 1, records_per_page: int = 10):
    params = {"page": page, "records_per_page": records_per_page}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}courses/controlled-courses", params=params, cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Создание курса
@client_app.post("/courses/create")
async def create_course_proxy(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BACKEND_URL}courses/create-course", json=body, cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Получение курса по ID
@client_app.get("/courses/{course_id}")
async def get_course_proxy(request: Request, course_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}courses/{course_id}", cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Разделы: создание
@client_app.post("/sections/create")
async def create_section_proxy(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BACKEND_URL}sections/create-section", json=body, cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Получение разделов курса
@client_app.get("/courses/{course_id}/sections")
async def get_sections_proxy(request: Request, course_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}sections/by_course/{course_id}", cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Темы: создание
@client_app.post("/topics/create")
async def create_topic_proxy(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BACKEND_URL}topics/create-topic", json=body, cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Получение тем раздела
@client_app.get("/sections/{section_id}/topics")
async def get_topics_proxy(request: Request, section_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}topics/by-section/{section_id}", cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Контент темы (сырой)
@client_app.get("/topics/{topic_id}/raw")
async def get_raw_content_proxy(request: Request, topic_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}topics/get-raw-content/{topic_id}", cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Обновление курса (PUT)
@client_app.put("/courses/{course_id}")
async def update_course_proxy(request: Request, course_id: str):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.put(f"{BACKEND_URL}courses/{course_id}", json=body, cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Удаление курса
@client_app.delete("/courses/{course_id}")
async def delete_course_proxy(request: Request, course_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.delete(f"{BACKEND_URL}courses/{course_id}", cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Запись на курс
@client_app.post("/courses/{course_id}/enroll")
async def enroll_course_proxy(request: Request, course_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BACKEND_URL}courses/{course_id}/enroll", cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Отписка от курса
@client_app.post("/courses/{course_id}/unenroll")
async def unenroll_course_proxy(request: Request, course_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BACKEND_URL}courses/{course_id}/unenroll", cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Обновление раздела (PUT)
@client_app.put("/sections/{section_id}")
async def update_section_proxy(request: Request, section_id: str):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.put(f"{BACKEND_URL}sections/{section_id}", json=body, cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Удаление раздела
@client_app.delete("/sections/{section_id}")
async def delete_section_proxy(request: Request, section_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.delete(f"{BACKEND_URL}sections/{section_id}", cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Обновление темы (через query-параметры, как в спецификации)
@client_app.put("/topics/{topic_id}")
async def update_topic_proxy(request: Request, topic_id: str, name: str = None, order_number: int = None):
    # Формируем URL с query-параметрами
    params = {}
    if name is not None:
        params["name"] = name
    if order_number is not None:
        params["order_number"] = order_number
    async with httpx.AsyncClient() as client:
        resp = await client.put(f"{BACKEND_URL}topics/{topic_id}", params=params, cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Удаление темы
@client_app.delete("/topics/{topic_id}")
async def delete_topic_proxy(request: Request, topic_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.delete(f"{BACKEND_URL}topics/{topic_id}", cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Рендеренный контент темы
@client_app.get("/topics/{topic_id}/rendered")
async def get_rendered_content_proxy(request: Request, topic_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}topics/get-rendered-content/{topic_id}", cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

# Установка контента темы (блоки)
@client_app.put("/topics/{topic_id}/content")
async def put_topic_content_proxy(request: Request, topic_id: str):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.put(f"{BACKEND_URL}topics/put-content/{topic_id}", json=body, cookies=request.cookies)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
