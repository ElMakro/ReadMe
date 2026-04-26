from fastapi import FastAPI
from fastapi import Response
from fastapi import status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

client_app = FastAPI()

client_app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@client_app.get("/client_healthcheck")
async def healthcheck():
    return Response(status_code=status.HTTP_200_OK)


@client_app.get("/")
async def main_page(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})
