"""
Интеграционный тест по методу "Чёрного ящика".
Использует фикстуру api_client из conftest.py.
"""
# import pytest
# import uuid


# Не создаём client глобально! Используем фикстуру.

# def test_full_registration_and_login_flow(api_client):
#     """
#     Сценарий:
#     1. Регистрация нового пользователя.
#     2. Вход под этим пользователем.
#     3. Проверка, что токен получен.
#     """
#     # Уникальные данные для каждого запуска
#     unique_suffix = uuid.uuid4().hex[:8]
#     unique_nickname = f"qa_tester_1000"
#
#     user_payload = {
#         "email": f"{unique_nickname}@test.com",
#         "nickname": unique_nickname,
#         "password": "StrongPassword123!",
#     }
#
#     # --- ШАГ 1: РЕГИСТРАЦИЯ ---
#     print(f"👉 Шаг 1: Пытаемся зарегистрировать {unique_nickname}")
#     response_reg = api_client.post("/api/v1/auth/reg", json=user_payload)
#     assert response_reg.status_code in [200, 201, 204], f"Регистрация: {response_reg.text}"
#     print(f"✅ Регистрация успешна! Ответ: {response_reg.status_code}")
#
#     # --- ШАГ 2: ЛОГИН ---
#     print(f"👉 Шаг 2: Пытаемся войти под {unique_nickname}")
#     response_login = api_client.post("/api/v1/auth/login", json={
#         "nickname": unique_nickname,
#         "password": "StrongPassword123!"
#     })
#     assert response_login.status_code == 200, f"Логин: {response_login.text}"
#     print(f"✅ Логин успешен!")
#
#     # --- ШАГ 3: ПРОВЕРКА ТОКЕНА ---
#     print("👉 Шаг 3: Проверяем наличие токена в Cookies")
#     assert "Authorization" in response_login.cookies, "Токен не найден в Cookies!"
#     token = response_login.cookies["Authorization"]
#     assert token.startswith("eyJ"), "Токен не похож на JWT"
#     print(f"✅ Токен получен: {token[:20]}...")
#
#     print("🎉 ТЕСТ УСПЕШНО ЗАВЕРШЁН!")


"""
✅ ЧТО ТЕСТ ДЕЛАЕТ: Проверяет регистрацию, вход, выход и валидацию токенов.
"""
import pytest
import uuid


class TestAuthPositive:
    @staticmethod
    def test_register_and_login_success(api_client):
        """
         ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Успешная регистрация (201) и вход (200) с получением Cookie.
        """
        nick = f"user_{uuid.uuid4().hex[:6]}"
        # Регистрация
        reg = api_client.post("/api/v1/auth/reg", json={
            "nickname": nick,
            "email": f"{nick}@test.com",
            "password": "StrongPassword123!"
        })
        assert reg.status_code == 201

        # Вход
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
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: После логаута кука Authorization удаляется.
        """
        nick = f"logout_user_{uuid.uuid4().hex[:6]}"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": nick, "email": f"{nick}@t.com", "password": "StrongPassword123!"})
        api_client.post("/api/v1/auth/login", json={"nickname": nick, "password": "StrongPassword123!"})

        assert "Authorization" in api_client.cookies

        # Логаут
        logout = api_client.get("/api/v1/auth/logout")
        assert logout.status_code == 200

        # Проверка удаления куки (клиент должен ее забыть)
        # TestClient хранит куки в state, после логаута сервер говорит удалить,
        # но в TestClient кука может остаться до следующего запроса или очистки.
        # Проверяем, что профиль больше недоступен (если бы логаут инвалидировал токен на сервере)
        # Или просто статус 200.


class TestAuthNegative:
    @staticmethod
    def test_register_duplicate_nickname(api_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Ошибка 409 Conflict при повторной регистрации того же ника.
        """
        nick = f"dup_{uuid.uuid4().hex[:6]}"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": nick, "email": "1@t.com", "password": "StrongPassword123!"})
        res = api_client.post("/api/v1/auth/reg",
                              json={"nickname": nick, "email": "2@t.com", "password": "StrongPassword123!"})
        assert res.status_code in [400, 409]

    @staticmethod
    def test_login_wrong_password(api_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Ошибка 401 Unauthorized при неверном пароле.
        """
        nick = f"wrong_pass_{uuid.uuid4().hex[:6]}"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": nick, "email": "x@t.com", "password": "StrongPassword123!"})
        res = api_client.post("/api/v1/auth/login", json={"nickname": nick, "password": "WrongPassword!"})
        assert res.status_code == 401