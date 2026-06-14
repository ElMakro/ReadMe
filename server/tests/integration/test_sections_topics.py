import uuid

import pytest


@pytest.fixture
def course_id(professor_client):
    res = professor_client.post(
        "/api/v1/courses/create-course", json={"name": f"Course_{uuid.uuid4().hex[:6]}", "is_public": True}
    )
    assert res.status_code == 201
    return res.json()["id"]


class TestSections:
    @staticmethod
    @pytest.mark.integration
    def test_create_section(professor_client, course_id):
        result = professor_client.post(
            "/api/v1/sections/create-section",
            json={"course_id": course_id, "name": "Section 1", "description": "Intro", "order_number": 1},
        )
        assert result.status_code == 201

    @staticmethod
    @pytest.mark.integration
    def test_get_sections_by_course(professor_client, course_id):
        create_result = professor_client.post(
            "/api/v1/sections/create-section",
            json={"course_id": course_id, "name": "S1", "description": "d", "order_number": 1},
        )
        assert create_result.status_code == 201

        result = professor_client.get(f"/api/v1/sections/by_course/{course_id}")
        assert result.status_code == 200
        assert len(result.json()) > 0

    @staticmethod
    @pytest.mark.integration
    def test_get_section_by_id(professor_client, course_id):
        section = professor_client.post(
            "/api/v1/sections/create-section",
            json={"course_id": course_id, "name": "GetMe", "description": "desc", "order_number": 1},
        )
        section_id = section.json()["id"]
        get = professor_client.get(f"/api/v1/sections/{section_id}")
        assert get.status_code == 200
        assert get.json()["name"] == "GetMe"


class TestTopics:
    @staticmethod
    @pytest.mark.integration
    def test_create_topic(professor_client, course_id):
        section_result = professor_client.post(
            "/api/v1/sections/create-section",
            json={"course_id": course_id, "name": "Sec", "description": "d", "order_number": 1},
        )
        assert section_result.status_code == 201
        section_id = section_result.json()["id"]
        result = professor_client.post(
            "/api/v1/topics/create-topic",
            json={"section_id": section_id, "name": "Topic 1", "order_number": 1, "raw_content": []},
        )
        assert result.status_code == 201, f"Не удалось создать тему: {result.text}"


class TestSectionUpdateDelete:
    @staticmethod
    @pytest.mark.integration
    def test_update_section(professor_client, course_id):
        section = professor_client.post(
            "/api/v1/sections/create-section",
            json={"course_id": course_id, "name": "Old Section", "description": "Desc", "order_number": 1},
        )
        assert section.status_code == 201, section.text
        section_id = section.json()["id"]
        update = professor_client.put(f"/api/v1/sections/{section_id}", json={"name": "New Section"})
        assert update.status_code == 204
        get = professor_client.get(f"/api/v1/sections/{section_id}")
        assert get.json()["name"] == "New Section"

    @staticmethod
    @pytest.mark.integration
    def test_delete_section(professor_client, course_id):
        section = professor_client.post(
            "/api/v1/sections/create-section",
            json={"course_id": course_id, "name": "Old Section", "description": "Desc", "order_number": 1},
        )
        section_id = section.json()["id"]
        delete = professor_client.delete(f"/api/v1/sections/{section_id}")
        assert delete.status_code == 204
        get = professor_client.get(f"/api/v1/sections/{section_id}")
        assert get.status_code == 404

    @staticmethod
    @pytest.mark.integration
    def test_swap_sections(professor_client, course_id):
        section_1 = professor_client.post(
            "/api/v1/sections/create-section",
            json={"course_id": course_id, "name": "First", "description": "Desc", "order_number": 1},
        ).json()["id"]
        section_2 = professor_client.post(
            "/api/v1/sections/create-section",
            json={"course_id": course_id, "name": "Second", "description": "Desc", "order_number": 2},
        ).json()["id"]
        swap = professor_client.put(
            "/api/v1/sections/swap", json={"first_element_id": section_1, "second_element_id": section_2}
        )
        assert swap.status_code == 204
        get_1 = professor_client.get(f"/api/v1/sections/{section_1}").json()
        get_2 = professor_client.get(f"/api/v1/sections/{section_2}").json()
        assert get_1["order_number"] == 2
        assert get_2["order_number"] == 1


class TestTopicUpdateDelete:
    @staticmethod
    @pytest.mark.integration
    def test_update_topic(professor_client, course_id):
        section = professor_client.post(
            "/api/v1/sections/create-section",
            json={"course_id": course_id, "name": "Sec", "description": "Desc", "order_number": 1},
        ).json()["id"]

        topic = professor_client.post(
            "/api/v1/topics/create-topic",
            json={"section_id": section, "name": "Old Topic", "order_number": 1, "raw_content": [], "tags": []},
        ).json()["id"]

        update = professor_client.put(
            f"/api/v1/topics/{topic}", json={"name": "New Topic", "tags": [], "raw_content": []}
        )
        assert update.status_code == 204, update.text

        get = professor_client.get(f"/api/v1/topics/{topic}").json()
        assert get["name"] == "New Topic"

    @staticmethod
    @pytest.mark.integration
    def test_delete_topic(professor_client, course_id):
        section = professor_client.post(
            "/api/v1/sections/create-section",
            json={"course_id": course_id, "name": "Old Section", "description": "Desc", "order_number": 1},
        ).json()["id"]
        topic = professor_client.post(
            "/api/v1/topics/create-topic",
            json={"section_id": section, "name": "Del", "order_number": 1, "raw_content": []},
        ).json()["id"]
        delete = professor_client.delete(f"/api/v1/topics/{topic}")
        assert delete.status_code == 204
        get = professor_client.get(f"/api/v1/topics/{topic}")
        assert get.status_code == 404
