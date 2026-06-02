"""
✅ ЧТО ТЕСТ ДЕЛАЕТ: Проверяет регистрацию, вход, выход и валидацию токенов.
"""
import pytest
import uuid


class TestAuthPositive:
    @staticmethod
    def test_register_and_login_success(api_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Успешная регистрация (201) и вход (200) с получением Cookie.
        """
        nick = f"user_{uuid.uuid4().hex[:6]}"
        reg = api_client.post("/api/v1/auth/reg", json={
            "nickname": nick,
            "email": f"{nick}@test.com",
            "password": "StrongPassword123!"
        })
        assert reg.status_code == 201

        login = api_client.post("/api/v1/auth/login", json={
            "nickname": nick,
            "password": "StrongPassword123!"
        })
        assert login.status_code == 200
        assert "Authorization" in login.cookies
        assert login.cookies["Authorization"].startswith("eyJ")

    @staticmethod
    def test_logout_clears_cookie(api_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: После логаута кука Authorization удаляется (или токен становится невалидным).
        """
        nick = f"logout_user_{uuid.uuid4().hex[:6]}"
        api_client.post("/api/v1/auth/reg", json={"nickname": nick, "email": f"{nick}@t.com", "password": "StrongPassword123!"})
        api_client.post("/api/v1/auth/login", json={"nickname": nick, "password": "StrongPassword123!"})
        assert "Authorization" in api_client.cookies

        logout = api_client.get("/api/v1/auth/logout")
        assert logout.status_code == 200
        # Проверка, что профиль больше недоступен (токен инвалидирован на сервере)
        profile_after = api_client.get("/api/v1/users/profile")
        assert profile_after.status_code == 401


class TestAuthNegative:
    @staticmethod
    def test_register_duplicate_nickname(api_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Ошибка 400/409 Conflict при повторной регистрации того же ника.
        """
        nick = f"dup_{uuid.uuid4().hex[:6]}"
        api_client.post("/api/v1/auth/reg", json={"nickname": nick, "email": "1@t.com", "password": "StrongPassword123!"})
        res = api_client.post("/api/v1/auth/reg", json={"nickname": nick, "email": "2@t.com", "password": "StrongPassword123!"})
        assert res.status_code in [400, 409]

    @staticmethod
    def test_login_wrong_password(api_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Ошибка 401 Unauthorized при неверном пароле.
        """
        nick = f"wrong_pass_{uuid.uuid4().hex[:6]}"
        api_client.post("/api/v1/auth/reg", json={"nickname": nick, "email": "x@t.com", "password": "StrongPassword123!"})
        res = api_client.post("/api/v1/auth/login", json={"nickname": nick, "password": "WrongPassword!"})
        assert res.status_code == 401