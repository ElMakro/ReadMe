"""
✅ ЧТО ТЕСТ ДЕЛАЕТ: Проверяет структуру курса: Разделы -> Темы.
"""
import pytest
import uuid


@pytest.fixture
def course_id(professor_client):
    """Создает курс и возвращает его ID"""
    res = professor_client.post("/api/v1/courses/create-course", json={
        "name": f"Course_{uuid.uuid4().hex[:6]}",
        "is_public": True
    })
    return res.json()["id"]


class TestSections:
    @staticmethod
    def test_create_section(professor_client, course_id):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Раздел создан (201).
        """
        res = professor_client.post("/api/v1/sections/create-section", json={
            "course_id": course_id,
            "name": "Section 1",
            "description": "Intro",
            "order_number": 1
        })
        assert res.status_code == 201
        return res.json()["id"]

    @staticmethod
    def test_get_sections_by_course(professor_client, course_id):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Список разделов получен (200).
        """
        professor_client.post("/api/v1/sections/create-section", json={
            "course_id": course_id, "name": "S1", "description": "d", "order_number": 1
        })
        res = professor_client.get(f"/api/v1/sections/by_course/{course_id}")
        assert res.status_code == 200
        assert len(res.json()) > 0


class TestTopics:
    @staticmethod
    def test_create_topic(professor_client, course_id):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Тема создана (201).
        """
        # Сначала создаем раздел
        sec_res = professor_client.post("/api/v1/sections/create-section", json={
            "course_id": course_id, "name": "Sec", "description": "d", "order_number": 1
        })
        sec_id = sec_res.json()["id"]

        # 🔧 Добавляем raw_content (пустой список блоков)
        res = professor_client.post("/api/v1/topics/create-topic", json={
            "section_id": sec_id,
            "name": "Topic 1",
            "order_number": 1,
            "raw_content": []  # ← Важно!
        })
        assert res.status_code == 201