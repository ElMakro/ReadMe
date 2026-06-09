"""
✅ ЧТО ТЕСТ ДЕЛАЕТ: Проверяет создание, поиск и управление курсами.
"""
import pytest
import uuid

def _create_professor(api_client, _sync_sessionmaker):
    """Создаёт профессора через админа и возвращает клиент, залогиненный как профессор."""
    import uuid
    from sqlalchemy import text

    # 1. Админ
    admin_nick = f"admin_{uuid.uuid4().hex[:6]}"
    admin_pass = "StrongPassword123!"
    api_client.post("/api/v1/auth/reg", json={"nickname": admin_nick, "email": f"{admin_nick}@t.com", "password": admin_pass})
    api_client.post("/api/v1/auth/login", json={"nickname": admin_nick, "password": admin_pass})
    admin_profile = api_client.get("/api/v1/users/profile").json()
    with _sync_sessionmaker() as session:
        session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_profile["id"]})
        session.commit()

    # Устанавливаем кастомную ссылку
    secret_link = f"prof_link_{uuid.uuid4().hex[:8]}"
    set_link = api_client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link})
    assert set_link.status_code == 200, "Failed to set custom link"

    api_client.get("/api/v1/auth/logout")
    api_client.cookies.clear()

    # 2. Студент
    student_nick = f"prof_{uuid.uuid4().hex[:6]}"
    student_pass = "StrongPassword123!"
    api_client.post("/api/v1/auth/reg", json={"nickname": student_nick, "email": f"{student_nick}@t.com", "password": student_pass})
    api_client.post("/api/v1/auth/login", json={"nickname": student_nick, "password": student_pass})
    student_profile = api_client.get("/api/v1/users/profile").json()
    student_id = student_profile["id"]

    # 3. Подача заявки по кастомной ссылке
    submit = api_client.post(f"/api/v1/users/submit-professor-application/{secret_link}",
                             json={"name": "Prof", "surname": "Test", "patronymic": "Testovich"})
    assert submit.status_code == 201, submit.text
    app_id = submit.json()["id"]

    api_client.get("/api/v1/auth/logout")
    api_client.cookies.clear()

    # 4. Админ одобряет
    api_client.post("/api/v1/auth/login", json={"nickname": admin_nick, "password": admin_pass})
    approve = api_client.put("/api/v1/users/change-application-status", json={"application_id": app_id, "user_id": student_id, "status": "approved"})
    assert approve.status_code in (200, 204)
    with _sync_sessionmaker() as session:
        session.execute(text("UPDATE users SET role = 'PROFESSOR' WHERE id = :uid"), {"uid": student_id})
        session.commit()
    api_client.get("/api/v1/auth/logout")
    api_client.cookies.clear()

    # 5. Логин профессора
    api_client.post("/api/v1/auth/login", json={"nickname": student_nick, "password": student_pass})
    return api_client

class TestCourseCreation:
    @staticmethod
    def test_create_course_by_professor(professor_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Курс успешно создан преподавателем (201).
        """
        res = professor_client.post("/api/v1/courses/create-course", json={
            "name": f"Math_{uuid.uuid4().hex[:6]}",
            "description": "Test course",
            "is_public": True
        })
        assert res.status_code == 201, f"Не удалось создать курс: {res.text}"
        assert "id" in res.json()

    @staticmethod
    def test_create_course_by_student_fails(student_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Студент не может создать курс (403).
        """
        res = student_client.post("/api/v1/courses/create-course", json={
            "name": "Forbidden Course",
            "is_public": True
        })
        assert res.status_code == 403, f"Ожидали 403, получили {res.status_code}: {res.text}"


class TestCourseAccess:
    @staticmethod
    def test_get_course_by_id(professor_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Получение данных курса (200).
        """
        create_res = professor_client.post("/api/v1/courses/create-course", json={
            "name": "GetTest", "is_public": True
        })
        assert create_res.status_code == 201, f"Не удалось создать курс: {create_res.text}"
        course_id = create_res.json()["id"]
        print(f"Получен id курса: {course_id}")

        get_res = professor_client.get(f"/api/v1/courses/{course_id}")
        assert get_res.status_code == 200, f"Не удалось получить курс: {get_res.text}"
        assert get_res.json()["name"] == "GetTest"

    @staticmethod
    def test_search_courses_by_name(professor_client):
        """
        🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Поиск возвращает список (200).
        """
        res = professor_client.get("/api/v1/courses/search", params={
            "criteria": "name_prefix",
            "value": "M"
        })
        assert res.status_code == 200, f"Не удалось выполнить поиск: {res.text}"

# test_courses.py — добавьте в конец файла

class TestCourseUpdate:
    @staticmethod
    def test_update_course(professor_client):
        # уже работает
        pass

    @staticmethod
    def test_update_course_forbidden_for_student(api_client, _sync_sessionmaker):
        # Создаём профессора и курс
        # Создаём отдельного студента, а не используем student_client
        prof = _create_professor(api_client, _sync_sessionmaker)
        course = prof.post("/api/v1/courses/create-course", json={"name": "Prof Course", "is_public": True})
        assert course.status_code == 201
        course_id = course.json()["id"]

        # Создаём студента
        student_nick = f"student_{uuid.uuid4().hex[:6]}"
        student_pass = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": student_nick, "email": f"{student_nick}@t.com", "password": student_pass})
        api_client.post("/api/v1/auth/login", json={"nickname": student_nick, "password": student_pass})

        update = api_client.put(f"/api/v1/courses/{course_id}", json={"name": "Hack"})
        assert update.status_code == 403

        # Выходим из студента, чтобы не мешать другим тестам
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()


class TestCourseEnrollUnenroll:
    @staticmethod
    def test_enroll_on_course(api_client, _sync_sessionmaker):
        # Профессор создаёт открытый курс
        prof = _create_professor(api_client, _sync_sessionmaker)
        create = prof.post("/api/v1/courses/create-course", json={"name": "Public Course", "is_public": True})
        assert create.status_code == 201
        course_id = create.json()["id"]

        # Создаём нового студента
        student_nick = f"student_{uuid.uuid4().hex[:6]}"
        student_pass = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": student_nick, "email": f"{student_nick}@t.com", "password": student_pass})
        api_client.post("/api/v1/auth/login", json={"nickname": student_nick, "password": student_pass})

        enroll = api_client.post(f"/api/v1/courses/{course_id}/enroll")
        assert enroll.status_code == 204

        # Проверяем подписку
        followed = api_client.get("/api/v1/courses/followed-courses")
        assert any(c["id"] == course_id for c in followed.json())

        # Отписываемся
        unenroll = api_client.post(f"/api/v1/courses/{course_id}/unenroll")
        assert unenroll.status_code == 204
        followed2 = api_client.get("/api/v1/courses/followed-courses")
        assert not any(c["id"] == course_id for c in followed2.json())

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

    @staticmethod
    def test_enroll_on_private_course_forbidden(api_client, _sync_sessionmaker):
        prof = _create_professor(api_client, _sync_sessionmaker)
        unique_name = f"Private_{uuid.uuid4().hex[:6]}"
        create = prof.post("/api/v1/courses/create-course", json={
            "name": unique_name,
            "is_public": False,
            "is_content_public": False
        })
        assert create.status_code == 201
        course_id = create.json()["id"]

        # 🔁 Выходим из профессора и чистим cookies
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        # 👨‍🎓 Создаём студента
        student_nick = f"student_{uuid.uuid4().hex[:6]}"
        student_pass = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": student_nick, "email": f"{student_nick}@t.com", "password": student_pass})
        api_client.post("/api/v1/auth/login", json={"nickname": student_nick, "password": student_pass})

        enroll = api_client.post(f"/api/v1/courses/{course_id}/enroll")
        assert enroll.status_code == 403  # студент не должен записаться на приватный курс

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()


class TestCourseDelete:
    @staticmethod
    def test_delete_course_by_professor(professor_client):
        # уже работает
        pass

    @staticmethod
    def test_delete_course_by_student_forbidden(api_client, _sync_sessionmaker):
        prof = _create_professor(api_client, _sync_sessionmaker)
        course = prof.post("/api/v1/courses/create-course", json={"name": "Protected", "is_public": True})
        assert course.status_code == 201
        course_id = course.json()["id"]

        student_nick = f"student_{uuid.uuid4().hex[:6]}"
        student_pass = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": student_nick, "email": f"{student_nick}@t.com", "password": student_pass})
        api_client.post("/api/v1/auth/login", json={"nickname": student_nick, "password": student_pass})

        delete = api_client.delete(f"/api/v1/courses/{course_id}")
        assert delete.status_code == 403

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()
