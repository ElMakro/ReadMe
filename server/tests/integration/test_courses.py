"""
✅ ЧТО ТЕСТ ДЕЛАЕТ: Проверяет создание, поиск и управление курсами.
"""
import pytest
import uuid


class TestCourseCreation:
    @staticmethod
    def test_create_course_by_professor(professor_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Курс успешно создан преподавателем (201).
        """
        res = professor_client.post("/api/v1/courses/create-course", json={
            "name": f"Math_{uuid.uuid4().hex[:6]}",
            "description": "Test course",
            "is_public": True
        })
        assert res.status_code == 201
        assert "id" in res.json()

    @staticmethod
    def test_create_course_by_student_fails(student_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Студент не может создать курс (403).
        """
        res = student_client.post("/api/v1/courses/create-course", json={
            "name": "Forbidden Course",
            "is_public": True
        })
        assert res.status_code == 403


class TestCourseAccess:
    @staticmethod
    def test_get_course_by_id(professor_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Получение данных курса (200).
        """
        create_res = professor_client.post("/api/v1/courses/create-course", json={
            "name": "GetTest", "is_public": True
        })
        course_id = create_res.json()["id"]

        get_res = professor_client.get(f"/api/v1/courses/{course_id}")
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "GetTest"

    @staticmethod
    def test_search_courses_by_name(professor_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Поиск возвращает список (200).
        """
        res = professor_client.get("/api/v1/courses/search", params={
            "criteria": "name_prefix",
            "value": "M"
        })
        assert res.status_code == 200