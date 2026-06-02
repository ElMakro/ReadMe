# # """
# # Интеграционный тест по методу "Чёрного ящика".
# # Мы не трогаем базу данных. Мы используем только API, как обычный пользователь.
# # """
# # import pytest
# # from fastapi.testclient import TestClient
# #
# # #  Импортируем ваше приложение (путь может отличаться, проверьте!)
# # from server.main import app
# #
# # # Создаем клиент для имитации браузера
# # client = TestClient(app)
# #
# #
# # def test_full_registration_and_login_flow():
# #     """
# #     Сценарий:
# #     1. Регистрация нового пользователя.
# #     2. Вход под этим пользователем.
# #     3. Проверка, что токен получен.
# #     """
# #
# #     # Данные для теста (можно менять на любые)
# #     unique_nickname = "qa_tester_5"
# #     user_payload = {
# #         "email": f"{unique_nickname}@test.com",
# #         "nickname": unique_nickname,
# #         "password": "StrongPassword123!",
# #     }
# #
# #     # --- ШАГ 1: РЕГИСТРАЦИЯ ---
# #     print(f"👉 Шаг 1: Пытаемся зарегистрировать {unique_nickname}")
# #
# #     # Отправляем POST запрос на эндпоинт регистрации
# #     # (Замените "/api/v1/auth/register" на реальный путь, если он отличается)
# #     response_reg = client.post("/api/v1/auth/reg", json=user_payload)
# #
# #     # Проверяем, что регистрация прошла успешно (обычно это 200 или 201)
# #     assert response_reg.status_code in [200, 201, 204], f"Регистрация провалилась: {response_reg.text}"
# #     print(f"✅ Регистрация успешна! Ответ сервера: {response_reg.status_code}")
# #
# #     # --- ШАГ 2: ЛОГИН ---
# #     print(f"👉 Шаг 2: Пытаемся войти под {unique_nickname}")
# #
# #     # Отправляем запрос на вход.
# #     # Внимание: Login часто принимает form-data (data=), а не json=, как Register.
# #     response_login = client.post("/api/v1/auth/login", json={
# #         "nickname": unique_nickname,
# #         "password": "StrongPassword123!"
# #     })
# #
# #     # Проверяем успешный вход
# #     assert response_login.status_code == 200, f"Логин провалился: {response_login.text}"
# #     print(f"✅ Логин успешен!")
# #
# #     # --- ШАГ 3: ПРОВЕРКА ТОКЕНА (JWT) ---
# #     print("👉 Шаг 3: Проверяем наличие токена в Cookies")
# #
# #     # В вашем проекте токен лежит в куках
# #     assert "Authorization" in response_login.cookies, "Токен не найден в Cookies!"
# #
# #     token = response_login.cookies["Authorization"]
# #     assert token.startswith("eyJ"), "Токен не похож на JWT (не начинается с eyJ)"
# #
# #     print(f"✅ Токен получен: {token[:20]}...")
# #     print("🎉 ТЕСТ УСПЕШНО ЗАВЕРШЕН!")
#
#
# # server/tests/integration/test_auth.py
# def test_full_registration_and_login_flow(api_client):
#     # 🔧 Проверка: создаём пользователя и сразу проверяем, что он в тестовой БД
#     import uuid
#     unique_suffix = uuid.uuid4().hex[:8]
#     unique_nickname = f"qa_tester_{unique_suffix}"
#
#     # Регистрация
#     response_reg = api_client.post("/api/v1/auth/reg", json={
#         "email": f"{unique_nickname}@test.com",
#         "nickname": unique_nickname,
#         "password": "StrongPassword123!",
#     })
#     assert response_reg.status_code in [200, 201], response_reg.text
#
#     # 🔧 Проверяем, что пользователь НЕ в основной БД (через прямой запрос к контейнеру)
#     # Это опционально, но даёт уверенность
#     print(f"✅ Регистрация успешна: {unique_nickname}")
#
#     # ЛОГИН
#     response_login = api_client.post("/api/v1/auth/login", json={
#         "nickname": unique_nickname,
#         "password": "StrongPassword123!"
#     })
#     assert response_login.status_code == 200, f"Логин провалился: {response_login.text}"
#     print(f"✅ Логин успешен!")
#
#     # ПРОВЕРКА ТОКЕНА
#     assert "Authorization" in response_login.cookies, "Токен не найден в Cookies!"
#
#     token = response_login.cookies["Authorization"]
#     assert token.startswith("eyJ"), "Токен не похож на JWT (не начинается с eyJ)"
#
#     print(f"✅ Токен получен: {token[:20]}...")
#     print("🎉 ТЕСТ УСПЕШНО ЗАВЕРШЕН!")
#
#     print("🎉 ТЕСТ ПРОШЁЛ!")

"""
Интеграционный тест по методу "Чёрного ящика".
Использует фикстуру api_client из conftest.py.
"""
import pytest
import uuid


# Не создаём client глобально! Используем фикстуру.

def test_full_registration_and_login_flow(api_client):
    """
    Сценарий:
    1. Регистрация нового пользователя.
    2. Вход под этим пользователем.
    3. Проверка, что токен получен.
    """
    # Уникальные данные для каждого запуска
    unique_suffix = uuid.uuid4().hex[:8]
    unique_nickname = f"qa_tester_1000"

    user_payload = {
        "email": f"{unique_nickname}@test.com",
        "nickname": unique_nickname,
        "password": "StrongPassword123!",
    }

    # --- ШАГ 1: РЕГИСТРАЦИЯ ---
    print(f"👉 Шаг 1: Пытаемся зарегистрировать {unique_nickname}")
    response_reg = api_client.post("/api/v1/auth/reg", json=user_payload)
    assert response_reg.status_code in [200, 201, 204], f"Регистрация: {response_reg.text}"
    print(f"✅ Регистрация успешна! Ответ: {response_reg.status_code}")

    # --- ШАГ 2: ЛОГИН ---
    print(f"👉 Шаг 2: Пытаемся войти под {unique_nickname}")
    response_login = api_client.post("/api/v1/auth/login", json={
        "nickname": unique_nickname,
        "password": "StrongPassword123!"
    })
    assert response_login.status_code == 200, f"Логин: {response_login.text}"
    print(f"✅ Логин успешен!")

    # --- ШАГ 3: ПРОВЕРКА ТОКЕНА ---
    print("👉 Шаг 3: Проверяем наличие токена в Cookies")
    assert "Authorization" in response_login.cookies, "Токен не найден в Cookies!"
    token = response_login.cookies["Authorization"]
    assert token.startswith("eyJ"), "Токен не похож на JWT"
    print(f"✅ Токен получен: {token[:20]}...")

    print("🎉 ТЕСТ УСПЕШНО ЗАВЕРШЁН!")