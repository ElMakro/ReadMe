# server/tests/integration/test_courses.py
"""
✅ ЧТО ТЕСТ ДЕЛАЕТ: Проверяет, что студент НЕ может создавать курсы (403).
"""
import pytest
import uuid


class TestCourseCreation:
    @staticmethod
    def test_create_course_by_student_fails(student_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Студент не может создать курс (403 Forbidden).
        """
        res = student_client.post("/api/v1/courses/create-course", json={
            "name": "Forbidden Course",
            "is_public": True
        })
        assert res.status_code == 403, f"Ожидали 403, получили {res.status_code}: {res.text}"