"""
✅ ЧТО ТЕСТ ДЕЛАЕТ: Проверяет конспекты к темам.
Используем professor_client для всех операций (упрощённая версия).
"""
import pytest
import uuid

from sqlalchemy import Uuid


@pytest.fixture
def topic_id_for_note(professor_client):
    """Создает курс -> раздел -> тему."""
    # Курс
    course_res = professor_client.post("/api/v1/courses/create-course", json={
        "name": "Название курса",
        "description": "Описание курса",
        "is_public": True,
        "is_content_public": True,
        "tags": ["Тег1"]
    })
    assert course_res.status_code == 201, f"Не удалось создать курс: {course_res.text}"
    course_id = course_res.json()["id"]
    courses = professor_client.get("/api/v1/courses/search", params={
            "criteria": "name_prefix",
            "value": "Note"
        })
    assert courses.status_code == 200
    # Раздел
    sec_res = professor_client.post("/api/v1/sections/create-section", json={
        "name": "S",
        "description": "d",
        "order_number": 1,
        "course_id": course_id
    })
    assert sec_res.status_code == 201, f"Не удалось создать раздел: {sec_res.text} {course_id} {courses.json()}"
    sec_id = sec_res.json()["id"]

    # Тема с пустым raw_content
    topic_res = professor_client.post("/api/v1/topics/create-topic", json={
        "section_id": sec_id,
        "name": "T",
        "order_number": 1,
        "raw_content": []
    })
    assert topic_res.status_code == 201, f"Не удалось создать тему: {topic_res.text}"
    return topic_res.json()["id"]


class TestNotes:
    @staticmethod
    def test_create_note(professor_client, topic_id_for_note):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Конспект создан (201).
        """
        res = professor_client.post("/api/v1/notes/create-note", json={
            "topic_id": topic_id_for_note,
            "name": "My Note",
            "content": "Hello World"
        })
        assert res.status_code == 201, f"Не удалось создать конспект: {res.text}"

    @staticmethod
    def test_get_my_notes(professor_client, topic_id_for_note):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Список конспектов пользователя (200).
        """
        # Сначала создаем
        professor_client.post("/api/v1/notes/create-note", json={
            "topic_id": topic_id_for_note,
            "name": "N",
            "content": "c"
        })

        res = professor_client.get("/api/v1/notes/my-notes")
        assert res.status_code == 200, f"Не удалось получить конспекты: {res.text}"
        assert len(res.json()) > 0

    @staticmethod
    def test_create_duplicate_note(professor_client, topic_id_for_note):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Нельзя создать два конспекта к одной теме (409).
        """
        professor_client.post("/api/v1/notes/create-note", json={
            "topic_id": topic_id_for_note,
            "name": "N1",
            "content": "c"
        })
        res = professor_client.post("/api/v1/notes/create-note", json={
            "topic_id": topic_id_for_note,
            "name": "N2",
            "content": "c"
        })
        assert res.status_code == 409, f"Ожидали 409, получили {res.status_code}: {res.text}"