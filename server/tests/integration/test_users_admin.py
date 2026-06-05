"""
✅ ЧТО ТЕСТ ДЕЛАЕТ: Тестирует заявки на роль преподавателя и их одобрение Админом.
"""
import pytest
import uuid


class TestProfessorApplication:
    @staticmethod
    def test_submit_application_success(student_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Заявка создана (201).
        """
        res = student_client.post("/api/v1/users/submit-professor-application", json={
            "name": "Иван",
            "surname": "Иванов"
        })
        assert res.status_code == 201
        assert "id" in res.json()

    @staticmethod
    def test_get_my_applications(student_client):
        """
        ✅ ЧТО ТЕСТ ДЕЛАЕТ: Студент подает заявку и проверяет список своих заявок.
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Список содержит хотя бы одну заявку (200).
        """
        student_client.post("/api/v1/users/submit-professor-application", json={
            "name": "Пётр", "surname": "Петров"
        })
        res = student_client.get("/api/v1/users/get-my-applications")
        assert res.status_code == 200
        assert len(res.json()) > 0

    @staticmethod
    def test_approve_application_changes_role(api_client, _sync_sessionmaker):
        """
        ✅ ЧТО ТЕСТ ДЕЛАЕТ (полный сценарий через API):
        1. Создаём админа с известными данными (через БД).
        2. Создаём студента, входим, подаём заявку, выходим.
        3. Входим как админ (зная логин/пароль).
        4. Одобряем заявку.
        5. Студент заходит заново и проверяет, что стал профессором.

        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Роль студента стала 'professor'.
        """
        import uuid
        from sqlalchemy import text

        # ========== ШАГ 0: Создаём админа с известными данными ==========
        admin_nick = f"admin_{uuid.uuid4().hex[:6]}"
        admin_password = "StrongPassword123!"

        # Регистрируем админа через API
        api_client.post("/api/v1/auth/reg", json={
            "nickname": admin_nick,
            "email": f"{admin_nick}@test.com",
            "password": admin_password
        })

        # Получаем ID админа
        api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nick,
            "password": admin_password
        })
        admin_profile = api_client.get("/api/v1/users/profile").json()
        admin_id = admin_profile["id"]

        # Меняем роль на ADMIN через БД
        with _sync_sessionmaker() as session:
            session.execute(
                text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"),
                {"uid": admin_id}
            )
            session.commit()

        # Выходим из админа
        api_client.get("/api/v1/auth/logout")

        # ========== ШАГ 1: Создаём студента и подаём заявку ==========
        student_nick = f"student_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"

        api_client.post("/api/v1/auth/reg", json={
            "nickname": student_nick,
            "email": f"{student_nick}@test.com",
            "password": student_password
        })
        api_client.post("/api/v1/auth/login", json={
            "nickname": student_nick,
            "password": student_password
        })

        submit_res = api_client.post("/api/v1/users/submit-professor-application", json={
            "name": "Сергей",
            "surname": "Сергеев"
        })
        assert submit_res.status_code == 201, f"Ошибка подачи заявки: {submit_res.text}"
        application_id = submit_res.json()["id"]

        student_profile = api_client.get("/api/v1/users/profile").json()
        student_id = student_profile["id"]

        # Студент выходит
        api_client.get("/api/v1/auth/logout")

        # ========== ШАГ 2: Входим как админ (зная логин/пароль!) ==========
        login_res = api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nick,
            "password": admin_password
        })
        assert login_res.status_code == 200, f"Ошибка входа админа: {login_res.text}"

        # Проверяем, что вошли как админ
        current_profile = api_client.get("/api/v1/users/profile").json()
        assert current_profile["role"] == "admin", f"Не админ! Роль: {current_profile['role']}"

        # ========== ШАГ 3: Админ одобряет заявку ==========
        approve_res = api_client.put("/api/v1/users/change-application-status", json={
            "application_id": application_id,
            "user_id": student_id,
            "status": "approved",
            "admin_comment": "Approved by QA test"
        })
        assert approve_res.status_code in [200, 204], \
            f"Ошибка одобрения заявки: {approve_res.status_code} {approve_res.text}"

        # Админ выходит
        api_client.get("/api/v1/auth/logout")

        # ========== ШАГ 4: Студент заходит заново и проверяет роль ==========
        login_res = api_client.post("/api/v1/auth/login", json={
            "nickname": student_nick,
            "password": student_password
        })
        assert login_res.status_code == 200, f"Ошибка входа студента: {login_res.text}"

        new_profile = api_client.get("/api/v1/users/profile").json()
        assert new_profile["role"] == "professor", \
            f"Роль не изменилась! Текущая: {new_profile['role']}"

        print("🎉 Тест пройден: студент стал преподавателем через полный API-сценарий!")