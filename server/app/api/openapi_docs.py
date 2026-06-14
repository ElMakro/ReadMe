openapi_extra_authorization_cookie_non_required = {
    "parameters": [
        {
            "name": "Authorization",
            "in": "cookie",
            "required": False,
            "description": "Шифрованный JWT токен, полученный при входе в систему.",
            "schema": {
                "type": "string",
                "example": "...",
            },
        },
    ],
}

openapi_extra_authorization_cookie_required = {
    "parameters": [
        {
            "name": "Authorization",
            "in": "cookie",
            "required": True,
            "description": "Шифрованный JWT токен, полученный при входе в систему.",
            "schema": {
                "type": "string",
                "example": "...",
            },
        },
    ],
    "responses": {
        401: {"description": "Авторизационный токен не обнаружен, или истёк, или некорректный"}
    }
}
