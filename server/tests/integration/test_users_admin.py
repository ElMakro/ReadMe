"""
✅ ЧТО ТЕСТ ДЕЛАЕТ: Тестирует заявки на роль преподавателя и их одобрение Админом.
Это критический путь для покрытия бизнес-логики пользователей.
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
        # 1. Подаем заявку
        student_client.post("/api/v1/users/submit-professor-application", json={
            "name": "Пётр", "surname": "Петров"
        })

        # 2. Получаем список
        res = student_client.get("/api/v1/users/get-my-applications")
        assert res.status_code == 200
        assert len(res.json()) > 0

    @staticmethod
    def test_approve_application_changes_role(admin_client, student_client):
        """
        ✅ ЧТО ТЕСТ ДЕЛАЕТ:
        1. Студент подает заявку.
        2. Админ одобряет заявку.
        3. Проверяем, что роль студента изменилась на 'professor'.
        """
        # 1. Студент подает заявку
        submit_res = student_client.post("/api/v1/users/submit-professor-application", json={
            "name": "Сергей",
            "surname": "Сергеев"
        })
        assert submit_res.status_code == 201, f"Ошибка подачи заявки: {submit_res.text}"
        application_id = submit_res.json()["id"]

        student_profile = student_client.get("/api/v1/users/profile").json()
        student_id = student_profile["id"]

        # 2. Админ одобряет заявку
        approve_res = admin_client.put("/api/v1/users/change-application-status", json={
            "application_id": application_id,
            "user_id": student_id,
            "status": "approved",
            "admin_comment": "Approved by QA test"
        })

        # Проверяем статус (может быть 204 или 200)
        assert approve_res.status_code in [200, 204], \
            f"Ожидали 200/204, получили {approve_res.status_code}: {approve_res.text}"

        # 3. Перелогиниваемся для обновления токена
        student_client.post("/api/v1/auth/login", json={
            "nickname": student_profile["nickname"],
            "password": "StrongPassword123!"
        })

        # 4. Проверяем профиль
        new_profile = student_client.get("/api/v1/users/profile").json()
        assert new_profile["role"] == "professor", \
            f"Роль не изменилась! Текущая: {new_profile['role']}"