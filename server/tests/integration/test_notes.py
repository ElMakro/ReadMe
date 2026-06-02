"""
✅ ЧТО ТЕСТ ДЕЛАЕТ: Проверяет конспекты студентов к темам.
"""
import pytest
import uuid


@pytest.fixture
def topic_id_for_note(professor_client, student_client):
    """Создает курс -> раздел -> тему. Студент записывается на курс."""
    # Курс
    course_res = professor_client.post("/api/v1/courses/create-course", json={
        "name": "NoteCourse",
        "is_public": True
    })
    course_id = course_res.json()["id"]

    # Студент записывается
    student_client.post(f"/api/v1/courses/{course_id}/enroll")

    # Раздел
    sec_res = professor_client.post("/api/v1/sections/create-section", json={
        "course_id": course_id,
        "name": "S",
        "description": "d",
        "order_number": 1
    })
    sec_id = sec_res.json()["id"]

    # Тема с пустым raw_content (избегаем ошибки compilation_manager)
    topic_res = professor_client.post("/api/v1/topics/create-topic", json={
        "section_id": sec_id,
        "name": "T",
        "order_number": 1,
        "raw_content": []  # ← Важно!
    })
    return topic_res.json()["id"]


class TestNotes:
    @staticmethod
    def test_create_note(student_client, topic_id_for_note):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Конспект создан (201).
        """
        res = student_client.post("/api/v1/notes/create-note", json={
            "topic_id": topic_id_for_note,
            "name": "My Note",
            "content": "Hello World"
        })
        assert res.status_code == 201

    @staticmethod
    def test_get_my_notes(student_client, topic_id_for_note):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Список конспектов пользователя (200).
        """
        # Сначала создаем
        student_client.post("/api/v1/notes/create-note", json={
            "topic_id": topic_id_for_note,
            "name": "N",
            "content": "c"
        })

        res = student_client.get("/api/v1/notes/my-notes")
        assert res.status_code == 200
        assert len(res.json()) > 0

    @staticmethod
    def test_create_duplicate_note(student_client, topic_id_for_note):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Нельзя создать два конспекта к одной теме (409).
        """
        student_client.post("/api/v1/notes/create-note", json={
            "topic_id": topic_id_for_note,
            "name": "N1",
            "content": "c"
        })
        res = student_client.post("/api/v1/notes/create-note", json={
            "topic_id": topic_id_for_note,
            "name": "N2",
            "content": "c"
        })
        assert res.status_code == 409