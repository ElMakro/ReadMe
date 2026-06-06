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
        assert res.status_code == 201, f"Не удалось создать курс: {res.text}"
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
        assert res.status_code == 403, f"Ожидали 403, получили {res.status_code}: {res.text}"


class TestCourseAccess:
    @staticmethod
    def test_get_course_by_id(professor_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Получение данных курса (200).
        """
        create_res = professor_client.post("/api/v1/courses/create-course", json={
            "name": "GetTest", "is_public": True
        })
        assert create_res.status_code == 201, f"Не удалось создать курс: {create_res.text}"
        course_id = create_res.json()["id"]
        print(f"Получен id курса: {course_id}")

        get_res = professor_client.get(f"/api/v1/courses/{course_id}")
        assert get_res.status_code == 200, f"Не удалось получить курс: {get_res.text}"
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
        assert res.status_code == 200, f"Не удалось выполнить поиск: {res.text}"