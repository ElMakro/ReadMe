openapi_extra_authorization_cookie = {
    "parameters": [
        {
            "name"       : "Authorization",
            "in"         : "cookie",
            "required"   : False,
            "description": "Шифрованный JWT токен, полученный при входе в систему.",
            "schema"     : {
                "type"   : "string",
                "example": "...",
            },
        },
    ],
}