# server/tests/integration/test_notes.py
"""
✅ ЧТО ТЕСТ ДЕЛАЕТ: Проверяет конспекты студентов к темам.
Примечание: для создания темы нужен преподаватель, поэтому этот тест пока пропускаем
или создаём тему через моки/фикстуры, если это критично.
"""
import pytest
import uuid


@pytest.mark.skip("Требует создания темы преподавателем — пока нет фикстуры для этого")
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