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
    assert res.status_code == 201, f"Не удалось создать курс: {res.text}"
    return res.json()["id"]


class TestSections:
    @staticmethod
    def test_create_section(professor_client, course_id):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Раздел создан (201).
        """
        print(f"Получен id курса: {course_id}")
        res = professor_client.post("/api/v1/sections/create-section", json={
            "course_id": course_id,
            "name": "Section 1",
            "description": "Intro",
            "order_number": 1
        })
        assert res.status_code == 201, f"Не удалось создать раздел: {res.text}"
        return res.json()["id"]

    @staticmethod
    def test_get_sections_by_course(professor_client, course_id):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Список разделов получен (200).
        """
        print(f"Получен id курса: {course_id}")
        create_res = professor_client.post("/api/v1/sections/create-section", json={
            "course_id": course_id, "name": "S1", "description": "d", "order_number": 1
        })
        assert create_res.status_code == 201, f"Не удалось создать раздел: {create_res.text}"

        res = professor_client.get(f"/api/v1/sections/by_course/{course_id}")
        assert res.status_code == 200, f"Не удалось получить разделы: {res.text}"
        assert len(res.json()) > 0


class TestTopics:
    @staticmethod
    def test_create_topic(professor_client, course_id):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Тема создана (201).
        """
        print(f"Получен id курса: {course_id}")
        # Сначала создаем раздел
        sec_res = professor_client.post("/api/v1/sections/create-section", json={
            "course_id": course_id, "name": "Sec", "description": "d", "order_number": 1
        })
        assert sec_res.status_code == 201, f"Не удалось создать раздел: {sec_res.text}"
        sec_id = sec_res.json()["id"]

        # 🔧 Добавляем raw_content (пустой список блоков)
        res = professor_client.post("/api/v1/topics/create-topic", json={
            "section_id": sec_id,
            "name": "Topic 1",
            "order_number": 1,
            "raw_content": []  # ← Важно!
        })
        assert res.status_code == 201, f"Не удалось создать тему: {res.text}"

# test_sections_topics.py — в конец файла

class TestSectionUpdateDelete:
    @staticmethod
    def test_update_section(professor_client, course_id):
        sec = professor_client.post("/api/v1/sections/create-section", json={
            "course_id": course_id,
            "name": "Old Section",
            "description": "Desc",  # добавлено
            "order_number": 1
        })
        assert sec.status_code == 201, sec.text
        sec_id = sec.json()["id"]
        # Обновляем
        update = professor_client.put(f"/api/v1/sections/{sec_id}", json={"name": "New Section"})
        assert update.status_code == 204
        # Проверяем
        get = professor_client.get(f"/api/v1/sections/{sec_id}")
        assert get.json()["name"] == "New Section"

    @staticmethod
    def test_delete_section(professor_client, course_id):
        sec = professor_client.post("/api/v1/sections/create-section", json={
            "course_id": course_id,
            "name": "Old Section",
            "description": "Desc",  # добавлено
            "order_number": 1
        })
        sec_id = sec.json()["id"]
        delete = professor_client.delete(f"/api/v1/sections/{sec_id}")
        assert delete.status_code == 204
        get = professor_client.get(f"/api/v1/sections/{sec_id}")
        assert get.status_code == 404

    @staticmethod
    def test_swap_sections(professor_client, course_id):
        # Создаём два раздела
        sec1 = professor_client.post("/api/v1/sections/create-section", json={
            "course_id": course_id, "name": "First", "description": "Desc", "order_number": 1
        }).json()["id"]
        sec2 = professor_client.post("/api/v1/sections/create-section", json={
            "course_id": course_id, "name": "Second", "description": "Desc", "order_number": 2
        }).json()["id"]
        # Меняем порядок
        swap = professor_client.put("/api/v1/sections/swap", json={
            "first_element_id": sec1, "second_element_id": sec2
        })
        assert swap.status_code == 204
        # Проверяем, что order_number поменялись
        get1 = professor_client.get(f"/api/v1/sections/{sec1}").json()
        get2 = professor_client.get(f"/api/v1/sections/{sec2}").json()
        assert get1["order_number"] == 2
        assert get2["order_number"] == 1


class TestTopicUpdateDelete:
    @staticmethod
    def test_update_topic(professor_client, course_id):
        sec = professor_client.post("/api/v1/sections/create-section", json={
            "course_id": course_id,
            "name": "Sec",
            "description": "Desc",
            "order_number": 1
        }).json()["id"]

        topic = professor_client.post("/api/v1/topics/create-topic", json={
            "section_id": sec,
            "name": "Old Topic",
            "order_number": 1,
            "raw_content": [],
            "tags": []
        }).json()["id"]

        # Обновляем с явным указанием всех полей модели
        update = professor_client.put(f"/api/v1/topics/{topic}", json={
            "name": "New Topic",
            "tags": [],
            "raw_content": []
        })
        assert update.status_code == 204, update.text

        get = professor_client.get(f"/api/v1/topics/{topic}").json()
        assert get["name"] == "New Topic"

    @staticmethod
    def test_delete_topic(professor_client, course_id):
        sec = professor_client.post("/api/v1/sections/create-section", json={
            "course_id": course_id,
            "name": "Old Section",
            "description": "Desc",  # добавлено
            "order_number": 1
        }).json()["id"]
        topic = professor_client.post("/api/v1/topics/create-topic", json={
            "section_id": sec, "name": "Del", "order_number": 1, "raw_content": []
        }).json()["id"]
        delete = professor_client.delete(f"/api/v1/topics/{topic}")
        assert delete.status_code == 204
        get = professor_client.get(f"/api/v1/topics/{topic}")
        assert get.status_code == 404