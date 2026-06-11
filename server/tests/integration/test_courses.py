import uuid
import pytest
from sqlalchemy import text

@pytest.mark.integration
def _create_professor(api_client, _sync_sessionmaker):
    admin_nickname = f"admin_{uuid.uuid4().hex[:6]}"
    admin_password = "StrongPassword123!"
    api_client.post("/api/v1/auth/reg", json={"nickname": admin_nickname, "email": f"{admin_nickname}@t.com", "password": admin_password})
    api_client.post("/api/v1/auth/login", json={"nickname": admin_nickname, "password": admin_password})
    admin_profile = api_client.get("/api/v1/users/profile").json()
    with _sync_sessionmaker() as session:
        session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_profile["id"]})
        session.commit()
    secret_link = f"prof_link_{uuid.uuid4().hex[:8]}"
    set_link = api_client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link})
    assert set_link.status_code == 200
    api_client.get("/api/v1/auth/logout")
    api_client.cookies.clear()
    student_nickname = f"prof_{uuid.uuid4().hex[:6]}"
    student_password = "StrongPassword123!"
    api_client.post("/api/v1/auth/reg", json={"nickname": student_nickname, "email": f"{student_nickname}@t.com", "password": student_password})
    api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})
    student_profile = api_client.get("/api/v1/users/profile").json()
    student_id = student_profile["id"]
    submit = api_client.post(f"/api/v1/users/submit-professor-application/{secret_link}",
                             json={"name": "Иван", "surname": "Иванов", "patronymic": "Иванович"})
    assert submit.status_code == 201
    app_id = submit.json()["id"]
    api_client.get("/api/v1/auth/logout")
    api_client.cookies.clear()
    api_client.post("/api/v1/auth/login", json={"nickname": admin_nickname, "password": admin_password})
    approve = api_client.put("/api/v1/users/change-application-status", json={"application_id": app_id, "user_id": student_id, "status": "approved"})
    assert approve.status_code == 204
    api_client.get("/api/v1/auth/logout")
    api_client.cookies.clear()
    api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})
    return api_client

class TestCourseCreation:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("name, description, is_public, is_content_public", [
        (f"Math_{uuid.uuid4().hex[:6]}", "Mathematics", True, True),
        (f"PE_{uuid.uuid4().hex[:6]}", "Programming engineering", True, True),
        (f"ML_{uuid.uuid4().hex[:6]}", "Machine learning", False, False),
        (f"BD_{uuid.uuid4().hex[:6]}", "Databases", True, False),
        (f"Eng_{uuid.uuid4().hex[:6]}", "English", False, False),
    ])
    def test_create_course_by_professor(professor_client, name, description, is_public, is_content_public):
        res = professor_client.post("/api/v1/courses/create-course", json={
            "name": name,
            "description": description,
            "is_public": is_public,
            "is_content_public": is_content_public
        })
        assert res.status_code == 201
        assert "id" in res.json()

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("name, is_public", [
        (f"Math_{uuid.uuid4().hex[:6]}", True),
        (f"PE_{uuid.uuid4().hex[:6]}", True),
        (f"ML_{uuid.uuid4().hex[:6]}", False),
        (f"BD_{uuid.uuid4().hex[:6]}", True),
        (f"Eng_{uuid.uuid4().hex[:6]}", False),
    ])
    def test_create_course_by_student_fails(student_client, name, is_public):
        res = student_client.post("/api/v1/courses/create-course", json={
            "name": name,
            "is_public": is_public
        })
        assert res.status_code == 403

class TestCourseAccess:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("name, is_public, is_content_public", [
        (f"Math_{uuid.uuid4().hex[:6]}", True, False),
        (f"PE_{uuid.uuid4().hex[:6]}", True, True),
        (f"ML_{uuid.uuid4().hex[:6]}", False, False),
        (f"BD_{uuid.uuid4().hex[:6]}", True, False),
        (f"Eng_{uuid.uuid4().hex[:6]}", False, False),
    ])
    def test_get_course_by_id(professor_client, name, is_public, is_content_public):
        create_res = professor_client.post("/api/v1/courses/create-course", json={
            "name": name, "is_public": is_public, "is_content_public": is_content_public
        })
        assert create_res.status_code == 201
        course_id = create_res.json()["id"]
        get_res = professor_client.get(f"/api/v1/courses/{course_id}")
        assert get_res.status_code == 200
        assert get_res.json()["name"] == name

    @staticmethod
    @pytest.mark.integration
    def test_search_courses_by_name(professor_client):
        res = professor_client.get("/api/v1/courses/search", params={
            "criteria": "name_prefix",
            "value": "M"
        })
        assert res.status_code == 200

class TestCourseUpdate:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("name, is_public, is_content_public", [
        (f"Math_{uuid.uuid4().hex[:6]}", True, True),
        (f"PE_{uuid.uuid4().hex[:6]}", True, False),
        (f"ML_{uuid.uuid4().hex[:6]}", False, False),
        (f"BD_{uuid.uuid4().hex[:6]}", True, True),
        (f"Eng_{uuid.uuid4().hex[:6]}", False, False),
    ])
    def test_update_course(api_client, _sync_sessionmaker, name, is_public, is_content_public):
        professor = _create_professor(api_client, _sync_sessionmaker)
        course = professor.post("/api/v1/courses/create-course", json={"name": name, "is_public": is_public, "is_content_public": is_content_public})
        assert course.status_code == 201
        course_id = course.json()["id"]
        update = professor.put(f"/api/v1/courses/{course_id}", json={"name": "Новое имя курса"})
        assert update.status_code == 204
        course_info = professor.get(f"/api/v1/courses/{course_id}")
        assert course_info.status_code == 200
        assert course_info.json()["name"] == "Новое имя курса"
        professor.get("/api/v1/auth/logout")
        professor.cookies.clear()

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("name, is_public, is_content_public", [
        (f"Math_{uuid.uuid4().hex[:6]}", True, False),
        (f"PE_{uuid.uuid4().hex[:6]}", True, False),
        (f"ML_{uuid.uuid4().hex[:6]}", False, False),
        (f"BD_{uuid.uuid4().hex[:6]}", True, True),
        (f"Eng_{uuid.uuid4().hex[:6]}", False, False),
    ])
    def test_update_course_forbidden_for_student(api_client, _sync_sessionmaker, name, is_public, is_content_public):
        professor = _create_professor(api_client, _sync_sessionmaker)
        course = professor.post("/api/v1/courses/create-course", json={"name": name, "is_public": is_public, "is_content_public": is_content_public})
        assert course.status_code == 201
        course_id = course.json()["id"]

        student_nickname = f"student_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": student_nickname, "email": f"{student_nickname}@t.com", "password": student_password})
        api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})

        update = api_client.put(f"/api/v1/courses/{course_id}", json={"name": "Hack"})
        assert update.status_code == 403

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

class TestCourseEnrollUnenroll:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("name, is_public", [
        (f"Math_{uuid.uuid4().hex[:6]}", True),
        (f"PE_{uuid.uuid4().hex[:6]}", True),
        (f"ML_{uuid.uuid4().hex[:6]}", True),
        (f"BD_{uuid.uuid4().hex[:6]}", True),
        (f"Eng_{uuid.uuid4().hex[:6]}", True),
    ])
    def test_enroll_on_course(api_client, _sync_sessionmaker, name, is_public):
        professor = _create_professor(api_client, _sync_sessionmaker)
        create = professor.post("/api/v1/courses/create-course", json={"name": name, "is_public": is_public})
        assert create.status_code == 201
        course_id = create.json()["id"]

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname = f"student_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": student_nickname, "email": f"{student_nickname}@t.com", "password": student_password})
        api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})

        get_course = api_client.get(f"/api/v1/courses/{course_id}")
        assert get_course.status_code == 200

        enroll = api_client.post(f"/api/v1/users/enroll?course_id={course_id}")
        assert enroll.status_code == 204

        followed = api_client.get("/api/v1/courses/followed-courses")
        assert any(c["id"] == course_id for c in followed.json())

        unenroll = api_client.delete(f"/api/v1/users/unenroll?course_id={course_id}")
        assert unenroll.status_code == 204
        followed2 = api_client.get("/api/v1/courses/followed-courses")
        assert not any(c["id"] == course_id for c in followed2.json())

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("name, is_public, is_content_public", [
        (f"Math_{uuid.uuid4().hex[:6]}", False, False),
        (f"PE_{uuid.uuid4().hex[:6]}", False, False),
        (f"ML_{uuid.uuid4().hex[:6]}", False, False),
        (f"BD_{uuid.uuid4().hex[:6]}", False, False),
        (f"Eng_{uuid.uuid4().hex[:6]}", False, False),
    ])
    def test_enroll_on_private_course_forbidden(api_client, _sync_sessionmaker, name, is_public, is_content_public):
        professor = _create_professor(api_client, _sync_sessionmaker)
        create = professor.post("/api/v1/courses/create-course", json={
            "name": name,
            "is_public": is_public,
            "is_content_public": is_content_public
        })
        assert create.status_code == 201
        course_id = create.json()["id"]

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname = f"student_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": student_nickname, "email": f"{student_nickname}@t.com", "password": student_password})
        api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})

        get_course = api_client.get(f"/api/v1/courses/{course_id}")
        assert get_course.status_code == 403

        enroll = api_client.post(f"/api/v1/users/enroll?course_id={course_id}")
        assert enroll.status_code == 403

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()


class TestCourseDelete:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("name, is_public, is_content_public", [
        (f"Math_{uuid.uuid4().hex[:6]}", True, True),
        (f"PE_{uuid.uuid4().hex[:6]}", True, False),
        (f"ML_{uuid.uuid4().hex[:6]}", False, False),
        (f"BD_{uuid.uuid4().hex[:6]}", False, False),
        (f"Eng_{uuid.uuid4().hex[:6]}", True, True),
    ])
    def test_delete_course_by_professor(api_client, _sync_sessionmaker, name, is_public, is_content_public):
        professor = _create_professor(api_client, _sync_sessionmaker)
        course = professor.post("/api/v1/courses/create-course", json={"name": name, "is_public": is_public, "is_content_public": is_content_public})
        assert course.status_code == 201
        course_id = course.json()["id"]
        delete = professor.delete(f"/api/v1/courses/{course_id}")
        assert delete.status_code == 204
        course_info = professor.get(f"/api/v1/courses/{course_id}")
        assert course_info.status_code == 404
        professor.get("/api/v1/auth/logout")
        professor.cookies.clear()

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("name, is_public, is_content_public", [
        (f"Math_{uuid.uuid4().hex[:6]}", True, True),
        (f"PE_{uuid.uuid4().hex[:6]}", True, False),
        (f"ML_{uuid.uuid4().hex[:6]}", False, False),
        (f"BD_{uuid.uuid4().hex[:6]}", False, False),
        (f"Eng_{uuid.uuid4().hex[:6]}", True, True),
    ])
    def test_delete_course_by_student_forbidden(api_client, _sync_sessionmaker, name, is_public, is_content_public):
        professor = _create_professor(api_client, _sync_sessionmaker)
        course = professor.post("/api/v1/courses/create-course", json={"name": name, "is_public": is_public, "is_content_public": is_content_public})
        assert course.status_code == 201
        course_id = course.json()["id"]

        student_nickname = f"student_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": student_nickname, "email": f"{student_nickname}@t.com", "password": student_password})
        api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})

        delete = api_client.delete(f"/api/v1/courses/{course_id}")
        assert delete.status_code == 403

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()
