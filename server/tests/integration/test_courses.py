import uuid

import pytest

from server.tests.integration.conftest import create_admin, create_professor, create_student


class TestCourseCreation:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "name, description, is_public, is_content_public",
        [
            (f"Math_{uuid.uuid4().hex[:6]}", "Mathematics", True, True),
            (f"PE_{uuid.uuid4().hex[:6]}", "Programming engineering", True, True),
            (f"ML_{uuid.uuid4().hex[:6]}", "Machine learning", False, False),
            (f"BD_{uuid.uuid4().hex[:6]}", "Databases", True, False),
            (f"Eng_{uuid.uuid4().hex[:6]}", "English", False, False),
        ],
    )
    def test_create_course_by_professor(professor_client, name, description, is_public, is_content_public):
        res = professor_client.post(
            "/api/v1/courses/create-course",
            json={
                "name": name,
                "description": description,
                "is_public": is_public,
                "is_content_public": is_content_public,
            },
        )
        assert res.status_code == 201
        assert "id" in res.json()

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "name, is_public",
        [
            (f"Math_{uuid.uuid4().hex[:6]}", True),
            (f"PE_{uuid.uuid4().hex[:6]}", True),
            (f"ML_{uuid.uuid4().hex[:6]}", False),
            (f"BD_{uuid.uuid4().hex[:6]}", True),
            (f"Eng_{uuid.uuid4().hex[:6]}", False),
        ],
    )
    def test_create_course_by_student_fails(student_client, name, is_public):
        res = student_client.post("/api/v1/courses/create-course", json={"name": name, "is_public": is_public})
        assert res.status_code == 403


class TestCourseAccess:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "name, is_public, is_content_public",
        [
            (f"Math_{uuid.uuid4().hex[:6]}", True, False),
            (f"PE_{uuid.uuid4().hex[:6]}", True, True),
            (f"ML_{uuid.uuid4().hex[:6]}", False, False),
            (f"BD_{uuid.uuid4().hex[:6]}", True, False),
            (f"Eng_{uuid.uuid4().hex[:6]}", False, False),
        ],
    )
    def test_get_course_by_id(professor_client, name, is_public, is_content_public):
        create_res = professor_client.post(
            "/api/v1/courses/create-course",
            json={"name": name, "is_public": is_public, "is_content_public": is_content_public},
        )
        assert create_res.status_code == 201
        course_id = create_res.json()["id"]
        get_res = professor_client.get(f"/api/v1/courses/{course_id}")
        assert get_res.status_code == 200
        assert get_res.json()["name"] == name

    @staticmethod
    @pytest.mark.integration
    def test_search_courses_by_name(professor_client):
        res = professor_client.get("/api/v1/courses/search", params={"criteria": "name_prefix", "value": "M"})
        assert res.status_code == 200


class TestCourseUpdate:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "name, is_public, is_content_public",
        [
            (f"Math_{uuid.uuid4().hex[:6]}", True, True),
            (f"PE_{uuid.uuid4().hex[:6]}", True, False),
            (f"ML_{uuid.uuid4().hex[:6]}", False, False),
            (f"BD_{uuid.uuid4().hex[:6]}", True, True),
            (f"Eng_{uuid.uuid4().hex[:6]}", False, False),
        ],
    )
    def test_update_course(professor_client, name, is_public, is_content_public):
        course = professor_client.post(
            "/api/v1/courses/create-course",
            json={"name": name, "is_public": is_public, "is_content_public": is_content_public},
        )
        assert course.status_code == 201
        course_id = course.json()["id"]
        update = professor_client.put(f"/api/v1/courses/{course_id}", json={"name": "Новое имя курса"})
        assert update.status_code == 204
        course_info = professor_client.get(f"/api/v1/courses/{course_id}")
        assert course_info.status_code == 200
        assert course_info.json()["name"] == "Новое имя курса"

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "name, is_public, is_content_public",
        [
            (f"Math_{uuid.uuid4().hex[:6]}", True, False),
            (f"PE_{uuid.uuid4().hex[:6]}", True, False),
            (f"ML_{uuid.uuid4().hex[:6]}", False, False),
            (f"BD_{uuid.uuid4().hex[:6]}", True, True),
            (f"Eng_{uuid.uuid4().hex[:6]}", False, False),
        ],
    )
    def test_update_course_forbidden_for_student(api_client, sync_sessionmaker, name, is_public, is_content_public):
        professor_nickname, professor_password = create_professor(api_client, sync_sessionmaker)
        api_client.post("/api/v1/auth/login", json={"nickname": professor_nickname, "password": professor_password})
        course = api_client.post(
            "/api/v1/courses/create-course",
            json={"name": name, "is_public": is_public, "is_content_public": is_content_public},
        )
        assert course.status_code == 201
        course_id = course.json()["id"]

        student_nickname, student_password = create_student(api_client)
        api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})

        update = api_client.put(f"/api/v1/courses/{course_id}", json={"name": "Hack"})
        assert update.status_code == 403

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()


class TestCourseEnrollUnenroll:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "name, is_public",
        [
            (f"Math_{uuid.uuid4().hex[:6]}", True),
            (f"PE_{uuid.uuid4().hex[:6]}", True),
            (f"ML_{uuid.uuid4().hex[:6]}", True),
            (f"BD_{uuid.uuid4().hex[:6]}", True),
            (f"Eng_{uuid.uuid4().hex[:6]}", True),
        ],
    )
    def test_enroll_on_course(api_client, sync_sessionmaker, name, is_public):
        professor_nickname, professor_password = create_professor(api_client, sync_sessionmaker)
        api_client.post("/api/v1/auth/login", json={"nickname": professor_nickname, "password": professor_password})
        create = api_client.post("/api/v1/courses/create-course", json={"name": name, "is_public": is_public})
        assert create.status_code == 201
        course_id = create.json()["id"]

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname, student_password = create_student(api_client)
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
    @pytest.mark.parametrize(
        "name, is_public, is_content_public",
        [
            (f"Math_{uuid.uuid4().hex[:6]}", False, False),
            (f"PE_{uuid.uuid4().hex[:6]}", False, False),
            (f"ML_{uuid.uuid4().hex[:6]}", False, False),
            (f"BD_{uuid.uuid4().hex[:6]}", False, False),
            (f"Eng_{uuid.uuid4().hex[:6]}", False, False),
        ],
    )
    def test_enroll_on_private_course_forbidden(api_client, sync_sessionmaker, name, is_public, is_content_public):
        professor_nickname, professor_password = create_professor(api_client, sync_sessionmaker)
        api_client.post("/api/v1/auth/login", json={"nickname": professor_nickname, "password": professor_password})
        create = api_client.post(
            "/api/v1/courses/create-course",
            json={"name": name, "is_public": is_public, "is_content_public": is_content_public},
        )
        assert create.status_code == 201
        course_id = create.json()["id"]

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname, student_password = create_student(api_client)
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
    @pytest.mark.parametrize(
        "name, is_public, is_content_public",
        [
            (f"Math_{uuid.uuid4().hex[:6]}", True, True),
            (f"PE_{uuid.uuid4().hex[:6]}", True, False),
            (f"ML_{uuid.uuid4().hex[:6]}", False, False),
            (f"BD_{uuid.uuid4().hex[:6]}", False, False),
            (f"Eng_{uuid.uuid4().hex[:6]}", True, True),
        ],
    )
    def test_delete_course_by_professor(professor_client, name, is_public, is_content_public):
        course = professor_client.post(
            "/api/v1/courses/create-course",
            json={"name": name, "is_public": is_public, "is_content_public": is_content_public},
        )
        assert course.status_code == 201
        course_id = course.json()["id"]
        delete = professor_client.delete(f"/api/v1/courses/{course_id}")
        assert delete.status_code == 204
        course_info = professor_client.get(f"/api/v1/courses/{course_id}")
        assert course_info.status_code == 404

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "name, is_public, is_content_public",
        [
            (f"Math_{uuid.uuid4().hex[:6]}", True, True),
            (f"PE_{uuid.uuid4().hex[:6]}", True, False),
            (f"ML_{uuid.uuid4().hex[:6]}", False, False),
            (f"BD_{uuid.uuid4().hex[:6]}", False, False),
            (f"Eng_{uuid.uuid4().hex[:6]}", True, True),
        ],
    )
    def test_delete_course_by_student_forbidden(api_client, sync_sessionmaker, name, is_public, is_content_public):
        professor_nickname, professor_password = create_professor(api_client, sync_sessionmaker)
        api_client.post("/api/v1/auth/login", json={"nickname": professor_nickname, "password": professor_password})
        course = api_client.post(
            "/api/v1/courses/create-course",
            json={"name": name, "is_public": is_public, "is_content_public": is_content_public},
        )
        assert course.status_code == 201
        course_id = course.json()["id"]

        student_nickname, student_password = create_student(api_client)
        api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})

        delete = api_client.delete(f"/api/v1/courses/{course_id}")
        assert delete.status_code == 403

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()


class TestControlledCourses:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "name, is_public, is_content_public",
        [
            (f"Math_{uuid.uuid4().hex[:6]}", True, True),
            (f"PE_{uuid.uuid4().hex[:6]}", True, False),
            (f"ML_{uuid.uuid4().hex[:6]}", False, False),
            (f"BD_{uuid.uuid4().hex[:6]}", False, False),
            (f"Eng_{uuid.uuid4().hex[:6]}", True, True),
        ],
    )
    def test_get_controlled_courses(professor_client, name, is_public, is_content_public):
        course = professor_client.post(
            "/api/v1/courses/create-course",
            json={"name": name, "is_public": is_public, "is_content_public": is_content_public},
        )
        assert course.status_code == 201
        res = professor_client.get("/api/v1/courses/controlled-courses")
        assert res.status_code == 200
        courses = res.json()
        assert len(courses) >= 1
        assert any(c["id"] == course.json()["id"] for c in courses)


class TestChangeProfessor:
    @staticmethod
    @pytest.mark.integration
    def test_change_course_professor(api_client, sync_sessionmaker):
        professor_a_nickname, professor_a_password = create_professor(api_client, sync_sessionmaker)
        api_client.post("/api/v1/auth/login", json={"nickname": professor_a_nickname, "password": professor_a_password})
        course = api_client.post("/api/v1/courses/create-course", json={"name": "CourseToTransfer", "is_public": True})
        assert course.status_code == 201
        course_id = course.json()["id"]

        admin_nickname, admin_password = create_admin(api_client, sync_sessionmaker)
        api_client.post("/api/v1/auth/login", json={"nickname": admin_nickname, "password": admin_password})
        secret_link = f"prof_link_{uuid.uuid4().hex[:8]}"
        set_link = api_client.post(
            "/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link}
        )
        assert set_link.status_code == 200
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        new_professor_nickname, new_professor_password = create_professor(api_client, sync_sessionmaker)
        api_client.post(
            "/api/v1/auth/login", json={"nickname": new_professor_nickname, "password": new_professor_password}
        )
        new_professor_profile = api_client.get("/api/v1/users/profile").json()
        new_professor_id = new_professor_profile["id"]
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        login_a = api_client.post(
            "/api/v1/auth/login", json={"nickname": professor_a_nickname, "password": professor_a_password}
        )
        assert login_a.status_code == 200

        change = api_client.put(
            f"/api/v1/courses/{course_id}/change-professor", json={"new_professor_id": new_professor_id}
        )
        assert change.status_code == 204

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        api_client.post(
            "/api/v1/auth/login", json={"nickname": new_professor_nickname, "password": new_professor_password}
        )
        get_course = api_client.get(f"/api/v1/courses/{course_id}").json()
        assert get_course["professor_id"] == new_professor_id


class TestCourseIcon:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "name, is_public, is_content_public",
        [
            (f"Math_{uuid.uuid4().hex[:6]}", True, True),
            (f"PE_{uuid.uuid4().hex[:6]}", True, False),
            (f"ML_{uuid.uuid4().hex[:6]}", False, False),
            (f"BD_{uuid.uuid4().hex[:6]}", False, False),
            (f"Eng_{uuid.uuid4().hex[:6]}", True, True),
        ],
    )
    def test_set_and_get_course_icon(professor_client, name, is_public, is_content_public):
        course = professor_client.post(
            "/api/v1/courses/create-course",
            json={"name": name, "is_public": is_public, "is_content_public": is_content_public},
        )
        course_id = course.json()["id"]
        files = {"icon_file": ("icon.png", b"fakeimage", "image/png")}
        set_icon = professor_client.post(f"/api/v1/courses/{course_id}/icon", files=files)
        assert set_icon.status_code == 204
        get_icon = professor_client.get(f"/api/v1/courses/{course_id}/icon")
        assert get_icon.status_code == 200
        assert get_icon.headers["content-type"] == "image/png"
