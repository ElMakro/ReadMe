import os

from fastapi import FastAPI, Request, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

STATIC_PATH = os.path.join(os.path.dirname(__file__), "static")
client_app = FastAPI()
client_app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")
templates = Jinja2Templates(directory="templates")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080/api/v1/")

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
async def course_page(request: Request, course_id: str):
    return templates.TemplateResponse(request, "course.html", {
        "request": request,
        "course_id": course_id,
        "api_base_url": BACKEND_URL
    })

@client_app.get("/me")
async def profile_page(request: Request):
    return templates.TemplateResponse(request, "profile.html", {
        "request": request,
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
    return templates.TemplateResponse(request, "course_creation/created_courses.html", {
        "request": request,
        "api_base_url": BACKEND_URL
    })

# @client_app.get("/create-course")
# async def create_course_form(request: Request):
#     return templates.TemplateResponse(request, "course_creation/course.html", {
#         "request": request,
#         "api_base_url": BACKEND_URL
#     })

@client_app.get("/course/{course_id}/sections")
async def edit_sections(request: Request, course_id: str):
    return templates.TemplateResponse(request, "course_creation/sections.html", {
        "request": request,
        "course_id": course_id,
        "api_base_url": BACKEND_URL
    })

@client_app.get("/course/{course_id}/section/{section_id}/topics")
async def edit_topics(request: Request, course_id: str, section_id: str):
    return templates.TemplateResponse(request, "course_creation/topics.html", {
        "request": request,
        "course_id": course_id,
        "section_id": section_id,
        "api_base_url": BACKEND_URL
    })

@client_app.get("/course/{course_id}/section/{section_id}/topic/{topic_id}/blocks")
async def edit_blocks(request: Request, course_id: str, section_id: str, topic_id: str):
    return templates.TemplateResponse(request, "course_creation/blocks.html", {
        "request": request,
        "course_id": course_id,
        "section_id": section_id,
        "topic_id": topic_id,
        "api_base_url": BACKEND_URL
    })

# @client_app.get("/course/{course_id}/edit")
# async def edit_course_page(request: Request, course_id: str):
#     return templates.TemplateResponse(request, "course_creation/course.html", {
#         "request": request,
#         "course_id": course_id,
#         "api_base_url": BACKEND_URL
#     })

@client_app.get("/my-notes")
async def my_notes_page(request: Request):
    return templates.TemplateResponse(request, "my_notes.html", {
        "request": request,
        "api_base_url": BACKEND_URL
    })

@client_app.get("/submit_professor_application")
async def submit_professor_application_form(request: Request):
    return templates.TemplateResponse(
        request,
        "submit_application.html",
        {
            "request": request,
            "api_base_url": BACKEND_URL
        }
    )

@client_app.get("/admin/applications")
async def admin_applications_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin_applications.html",
        {
            "request": request,
            "api_base_url": BACKEND_URL
        }
    )


@client_app.get("/my-applications")
async def my_applications_page(request: Request):
    return templates.TemplateResponse(
        request,
        "my_applications.html",
        {
            "request": request,
            "api_base_url": BACKEND_URL
        }
    )


@client_app.get("/admin/users")
async def admin_users_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin_users.html",
        {
            "request": request,
            "api_base_url": BACKEND_URL
        }
    )
