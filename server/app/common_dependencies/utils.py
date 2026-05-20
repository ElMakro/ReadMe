from typing import NamedTuple

from fastapi import Request


class CreatedTokenTuple(NamedTuple):
    encoded_jwt: str
    session_id: str


async def get_token_from_cookies(request: Request) -> str | None:
    token = request.cookies.get("Authorization")
    return token
