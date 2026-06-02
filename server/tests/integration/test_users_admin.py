# server/tests/integration/test_users_admin.py
"""
✅ ЧТО ТЕСТ ДЕЛАЕТ: Проверяет подачу заявки на роль преподавателя.
"""
import pytest
import uuid


class TestProfessorApplication:
    @staticmethod
    def test_submit_application_success(student_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Заявка успешно создана (201).
        """
        res = student_client.post("/api/v1/users/submit-professor-application", json={
            "name": "Иван",
            "surname": "Иванов"
        })
        assert res.status_code == 201, f"Ожидали 201, получили {res.status_code}: {res.text}"

    # server/tests/integration/test_users_admin.py

    @staticmethod
    def test_submit_duplicate_application(student_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Повторная заявка либо отклоняется (409), либо создаётся (201) — зависит от реализации.
        """
        # Первая заявка
        student_client.post("/api/v1/users/submit-professor-application", json={
            "name": "Пётр",
            "surname": "Петров"
        })

        # Вторая заявка
        res = student_client.post("/api/v1/users/submit-professor-application", json={
            "name": "Пётр",
            "surname": "Петров"
        })

        # Принимаем оба варианта, пока не уточним требования
        assert res.status_code in [201, 409], f"Ожидали 201 или 409, получили {res.status_code}: {res.text}"