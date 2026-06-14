import pytest


@pytest.fixture
def topic_id_for_note(professor_client):
    course_result = professor_client.post(
        "/api/v1/courses/create-course",
        json={
            "name": "Название курса",
            "description": "Описание курса",
            "is_public": True,
            "is_content_public": True,
            "tags": ["Тег1"],
        },
    )
    assert course_result.status_code == 201
    course_id = course_result.json()["id"]
    courses = professor_client.get("/api/v1/courses/search", params={"criteria": "name_prefix", "value": "Note"})
    assert courses.status_code == 200
    section_result = professor_client.post(
        "/api/v1/sections/create-section",
        json={"name": "S", "description": "d", "order_number": 1, "course_id": course_id},
    )
    assert section_result.status_code == 201
    section_id = section_result.json()["id"]
    topic_result = professor_client.post(
        "/api/v1/topics/create-topic",
        json={"section_id": section_id, "name": "T", "order_number": 1, "raw_content": []},
    )
    assert topic_result.status_code == 201
    return topic_result.json()["id"]


class TestNotes:
    @staticmethod
    @pytest.mark.integration
    def test_create_note(professor_client, topic_id_for_note):
        result = professor_client.post(
            "/api/v1/notes/create-note",
            json={"topic_id": topic_id_for_note, "name": "My Note", "content": "Hello World"},
        )
        assert result.status_code == 201

    @staticmethod
    @pytest.mark.integration
    def test_get_my_notes(professor_client, topic_id_for_note):
        professor_client.post(
            "/api/v1/notes/create-note", json={"topic_id": topic_id_for_note, "name": "N", "content": "c"}
        )

        result = professor_client.get("/api/v1/notes/my-notes")
        assert result.status_code == 200
        assert len(result.json()) > 0

    @staticmethod
    @pytest.mark.integration
    def test_create_duplicate_note(professor_client, topic_id_for_note):
        professor_client.post(
            "/api/v1/notes/create-note", json={"topic_id": topic_id_for_note, "name": "N1", "content": "c"}
        )
        result = professor_client.post(
            "/api/v1/notes/create-note", json={"topic_id": topic_id_for_note, "name": "N2", "content": "c"}
        )
        assert result.status_code == 409


class TestNoteOperations:
    @staticmethod
    @pytest.mark.integration
    def test_get_note_for_topic(professor_client, topic_id_for_note):
        create = professor_client.post(
            "/api/v1/notes/create-note",
            json={"topic_id": topic_id_for_note, "name": "Note to get", "content": "Content"},
        )
        assert create.status_code == 201
        get = professor_client.get(f"/api/v1/notes/get-note-for-topic/{topic_id_for_note}")
        assert get.status_code == 200
        assert get.json()["name"] == "Note to get"

    @staticmethod
    @pytest.mark.integration
    def test_update_note(professor_client, topic_id_for_note):
        create = professor_client.post(
            "/api/v1/notes/create-note", json={"topic_id": topic_id_for_note, "name": "Old", "content": "Old content"}
        )
        note_id = create.json()["id"]
        update = professor_client.put(
            "/api/v1/notes/update-note",
            json={"note_id": note_id, "topic_id": topic_id_for_note, "name": "New", "content": "New content"},
        )
        assert update.status_code == 204
        get = professor_client.get(f"/api/v1/notes/get-note-for-topic/{topic_id_for_note}")
        assert get.json()["name"] == "New"
        assert get.json()["content"] == "New content"

    @staticmethod
    @pytest.mark.integration
    def test_delete_note(professor_client, topic_id_for_note):
        create = professor_client.post(
            "/api/v1/notes/create-note", json={"topic_id": topic_id_for_note, "name": "ToDelete", "content": "Content"}
        )
        note_id = create.json()["id"]
        delete = professor_client.delete(f"/api/v1/notes/delete-note/{note_id}")
        assert delete.status_code == 204
        get = professor_client.get(f"/api/v1/notes/get-note-for-topic/{topic_id_for_note}")
        assert get.status_code == 204
