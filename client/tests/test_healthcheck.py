from fastapi import status

from client.main import healthcheck


async def test_client_healthcheck():
    response = await healthcheck()

    assert response.status_code == status.HTTP_200_OK
