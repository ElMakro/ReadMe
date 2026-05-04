from fastapi import status

from server.main import healthcheck


async def test_server_healthcheck():
    response = await healthcheck()

    assert response.status_code == status.HTTP_200_OK
