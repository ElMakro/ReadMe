from fastapi import FastAPI
from fastapi import Response
from fastapi import status

app = FastAPI()

@app.get("/server_healthcheck")
async def healthcheck():
    return Response(status_code=status.HTTP_200_OK)
