import uuid
import pytest


@pytest.mark.integration
def test_upload_and_get_topic_resource(professor_client):
    course = professor_client.post("/api/v1/courses/create-course", json={
        "name": f"ResourceCourse_{uuid.uuid4().hex[:6]}",
        "is_public": True
    })
    assert course.status_code == 201
    course_id = course.json()["id"]

    section = professor_client.post("/api/v1/sections/create-section", json={
        "course_id": course_id,
        "name": "Test Section",
        "description": "Section for resource test",
        "order_number": 1
    })
    assert section.status_code == 201
    section_id = section.json()["id"]

    filename = "test.txt"
    topic_data = {
        "section_id": section_id,
        "name": "Topic with file",
        "order_number": 1,
        "raw_content": [
            {
                "type": "files",
                "content": [{"original_filename": filename}]
            }
        ]
    }
    create_topic = professor_client.post("/api/v1/topics/create-topic", json=topic_data)
    assert create_topic.status_code == 201
    topic_id = create_topic.json()["id"]

    files = {"resource": ("test.txt", b"Hello, world!", "text/plain")}
    upload = professor_client.post(
        f"/api/v1/topics/upload-resource/{topic_id}/1/1",
        files=files
    )
    assert upload.status_code == 200
    upload_data = upload.json()
    server_filename = upload_data["server_filename"]
    assert server_filename is not None

    get_res = professor_client.get(f"/api/v1/topics/get-resource/{topic_id}/{server_filename}")
    assert get_res.status_code == 200
    assert get_res.text == "Hello, world!"
    assert get_res.headers["content-type"] == "text/plain; charset=utf-8"

    get_original = professor_client.get(f"/api/v1/topics/get-resource/{topic_id}/test.txt")
    assert get_original.status_code == 404

@pytest.mark.integration
def test_upload_resource_wrong_block_type(professor_client):
    course = professor_client.post("/api/v1/courses/create-course", json={
        "name": f"MarkdownCourse_{uuid.uuid4().hex[:6]}",
        "is_public": True
    })
    assert course.status_code == 201
    course_id = course.json()["id"]

    section = professor_client.post("/api/v1/sections/create-section", json={
        "course_id": course_id,
        "name": "Section",
        "description": "desc",
        "order_number": 1
    })
    assert section.status_code == 201
    section_id = section.json()["id"]

    topic_data = {
        "section_id": section_id,
        "name": "Markdown Topic",
        "order_number": 1,
        "raw_content": [{"type": "markdown", "content": ["# Hello"]}]
    }
    topic = professor_client.post("/api/v1/topics/create-topic", json=topic_data)
    assert topic.status_code == 201
    topic_id = topic.json()["id"]

    files = {"resource": ("file.txt", b"data", "text/plain")}
    upload = professor_client.post(f"/api/v1/topics/upload-resource/{topic_id}/1/1", files=files)
    assert upload.status_code == 400
    assert "не позволяет хранить файлы" in upload.text