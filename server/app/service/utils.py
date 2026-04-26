from fastapi import HTTPException, Request, status


async def get_token_from_cookies(request: Request) -> str:
    token = request.cookies.get("Authorization")
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не обнаружен."
        )
    return token
