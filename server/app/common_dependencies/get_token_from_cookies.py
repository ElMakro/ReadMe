from fastapi import Request


async def get_token_from_cookies(request: Request) -> str | None:
    token = request.cookies.get("Authorization")
    return token
