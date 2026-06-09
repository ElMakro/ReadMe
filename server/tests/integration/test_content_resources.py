# test_content_resources.py
import uuid

def test_get_topic_resource_not_found(professor_client):
    course = professor_client.post("/api/v1/courses/create-course", json={"name": "ResCourse", "is_public": True})
    assert course.status_code == 201, course.text
    course_id = course.json()["id"]
    section = professor_client.post("/api/v1/sections/create-section", json={
        "course_id": course_id,
        "name": "Sec",
        "description": "Description",  # добавлено
        "order_number": 1
    })
    assert section.status_code == 201, section.text
    sec_id = section.json()["id"]
    topic = professor_client.post("/api/v1/topics/create-topic", json={"section_id": sec_id, "name": "Topic", "order_number": 1, "raw_content": []})
    assert topic.status_code == 201, topic.text
    topic_id = topic.json()["id"]
    res = professor_client.get("/api/v1/content/get-topic-resource", params={"topic_id": topic_id, "resource_filename": "nonexistent.png"})
    assert res.status_code == 404