import uuid
import os
import pytest
from server.tests.integration.conftest import create_student, create_admin, create_professor


DEFAULT_SECRET_LINK = os.getenv("DEFAULT_SECRET_APPLICATION_LINK_PART", "submit_professor_application")


class TestActiveApplications:
    @staticmethod
    @pytest.mark.integration
    def test_get_active_applications(api_client, sync_sessionmaker):
        admin_nickname, admin_password = create_admin(api_client, sync_sessionmaker)
        api_client.post("/api/v1/auth/login", json={"nickname": admin_nickname, "password": admin_password})
        secret_link = f"active_test_link_{uuid.uuid4().hex[:8]}"
        set_link = api_client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link})
        assert set_link.status_code == 200
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        first_student_nickname, first_student_password = create_student(api_client)
        api_client.post("/api/v1/auth/login", json={"nickname": first_student_nickname, "password": first_student_password})
        submit = api_client.post(f"/api/v1/users/submit-professor-application/{secret_link}", json={"name": "Ivan", "surname": "Ivanov"})
        assert submit.status_code == 201
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        second_student_nickname, second_student_password = create_student(api_client)
        api_client.post("/api/v1/auth/login",
                        json={"nickname": second_student_nickname, "password": second_student_password})
        submit = api_client.post(f"/api/v1/users/submit-professor-application/{secret_link}",
                                 json={"name": "Petr", "surname": "Petrov"})
        assert submit.status_code == 201
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()
        api_client.post("/api/v1/auth/login", json={"nickname": admin_nickname, "password": admin_password})
        active_applications = api_client.get("/api/v1/users/get-active-applications")
        assert active_applications.status_code == 200
        assert len(active_applications.json()) == 2

class TestProfessorApplication:
    @staticmethod
    @pytest.mark.integration
    def test_submit_application_success(api_client, sync_sessionmaker):
        admin_nickname, admin_password = create_admin(api_client, sync_sessionmaker)
        api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nickname,
            "password": admin_password
        })

        secret_link = f"test_link_{uuid.uuid4().hex[:6]}"
        set_result = api_client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link})
        assert set_result.status_code == 200

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname, student_password = create_student(api_client)
        api_client.post("/api/v1/auth/login", json={
            "nickname": student_nickname,
            "password": student_password
        })

        result = api_client.post(f"/api/v1/users/submit-professor-application/{secret_link}", json={
            "name": "Иван",
            "surname": "Иванов"
        })
        assert result.status_code == 201
        assert "id" in result.json()

    @staticmethod
    @pytest.mark.integration
    def test_get_my_applications(api_client, sync_sessionmaker):
        admin_nickname, admin_password = create_admin(api_client, sync_sessionmaker)
        api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nickname,
            "password": admin_password
        })
        secret_link = f"test_link_{uuid.uuid4().hex[:6]}"
        set_result = api_client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link})
        assert set_result.status_code == 200

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname, student_password = create_student(api_client)
        api_client.post("/api/v1/auth/login", json={
            "nickname": student_nickname,
            "password": student_password
        })

        submit_result = api_client.post(f"/api/v1/users/submit-professor-application/{secret_link}", json={
            "name": "Пётр", "surname": "Петров"
        })
        assert submit_result.status_code == 201

        result = api_client.get("/api/v1/users/get-my-applications")
        assert result.status_code == 200
        applications = result.json()
        assert len(applications) > 0
        found = any(app["application_id"] == submit_result.json()["id"] for app in applications)
        assert found, "Созданная заявка не найдена в списке"

    @staticmethod
    @pytest.mark.integration
    def test_approve_application_changes_role(api_client, sync_sessionmaker):
        admin_nickname, admin_password = create_admin(api_client, sync_sessionmaker)
        api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nickname,
            "password": admin_password
        })

        secret_link = "test_approve_link"
        set_result = api_client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link})
        assert set_result.status_code == 200

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname, student_password = create_student(api_client)
        api_client.post("/api/v1/auth/login", json={
            "nickname": student_nickname,
            "password": student_password
        })
        student_profile = api_client.get("/api/v1/users/profile").json()
        student_id = student_profile["id"]

        submit_result = api_client.post(f"/api/v1/users/submit-professor-application/{secret_link}", json={
            "name": "Сергей",
            "surname": "Сергеев"
        })
        assert submit_result.status_code == 201
        app_id = submit_result.json()["id"]

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nickname,
            "password": admin_password
        })
        approve_result = api_client.put("/api/v1/users/change-application-status", json={
            "application_id": app_id,
            "user_id": student_id,
            "status": "approved"
        })
        assert approve_result.status_code == 204

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        login_result = api_client.post("/api/v1/auth/login", json={
            "nickname": student_nickname,
            "password": student_password
        })
        assert login_result.status_code == 200
        new_profile = api_client.get("/api/v1/users/profile").json()
        assert new_profile["role"] == "professor"

class TestAdminUserManagement:
    @staticmethod
    @pytest.mark.integration
    def test_get_all_users(admin_client):
        result = admin_client.get("/api/v1/users/all")
        assert result.status_code == 200
        assert len(result.json()) >= 1

    @staticmethod
    @pytest.mark.integration
    def test_change_user_role(api_client, sync_sessionmaker):
        admin_nickname, admin_password = create_admin(api_client, sync_sessionmaker)
        student_nickname, student_password = create_student(api_client)
        api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})
        student_profile = api_client.get("/api/v1/users/profile").json()
        student_id = student_profile["id"]
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        api_client.post("/api/v1/auth/login", json={"nickname": admin_nickname, "password": admin_password})
        change = api_client.put("/api/v1/users/change-role", json={"id": student_id, "role": "admin"})
        assert change.status_code == 204

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})
        student_profile = api_client.get("/api/v1/users/profile")
        assert student_profile.json()["role"] == "admin"

    @staticmethod
    @pytest.mark.integration
    def test_delete_user(api_client, sync_sessionmaker):
        admin_nickname, admin_password = create_admin(api_client, sync_sessionmaker)
        student_nickname, student_password = create_student(api_client)
        api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})
        student_profile = api_client.get("/api/v1/users/profile").json()
        student_id = student_profile["id"]
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        api_client.post("/api/v1/auth/login", json={"nickname": admin_nickname, "password": admin_password})
        delete = api_client.delete(f"/api/v1/users/delete-user/{student_id}")
        assert delete.status_code == 204
        deleted_student = api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})
        assert deleted_student.status_code == 401

class TestUserProfileUpdate:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("new_nickname", [
        f"Updated_{uuid.uuid4().hex[:6]}",
        f"Updated_{uuid.uuid4().hex[:6]}",
        f"Updated_{uuid.uuid4().hex[:6]}",
        f"Updated_{uuid.uuid4().hex[:6]}",
        f"Updated_{uuid.uuid4().hex[:6]}",
    ])
    def test_update_profile(student_client, new_nickname):
        update = student_client.put("/api/v1/users/profile", json={"nickname": new_nickname, "email": f"{new_nickname}@new.com"})
        assert update.status_code == 200
        profile = student_client.get("/api/v1/users/profile").json()
        assert profile["nickname"] == new_nickname
        assert profile["email"] == f"{new_nickname}@new.com"

class TestUserSearch:
    @staticmethod
    @pytest.mark.integration
    def test_search_users(api_client, sync_sessionmaker):
        admin_nickname, admin_password = create_admin(api_client, sync_sessionmaker)
        unique = uuid.uuid4().hex[:6]
        nickname = f"searchme_{unique}"
        reg = api_client.post("/api/v1/auth/reg", json={"nickname": nickname, "email": f"{nickname}@t.com", "password": "StrongPassword123!"})
        assert reg.status_code == 201, f"Регистрация не удалась: {reg.text}"
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        api_client.post(
            "/api/v1/auth/login", json={"nickname": admin_nickname, "password": admin_password})

        res = api_client.get("/api/v1/users/search", params={"search_pattern": nickname})
        assert res.status_code == 200
        users = res.json()
        assert any(u["nickname"] == nickname for u in users)

class TestEnrolledUsers:
    @staticmethod
    @pytest.mark.integration
    def test_get_enrolled_users(api_client, sync_sessionmaker):
        professor_nickname, professor_password = create_professor(api_client, sync_sessionmaker)
        course = api_client.post("/api/v1/courses/create-course", json={"name": "EnrollTest", "is_public": True})
        assert course.status_code == 201
        course_id = course.json()["id"]
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname, student_password = create_student(api_client)
        api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})
        enroll = api_client.post(f"/api/v1/users/enroll?course_id={course_id}")
        assert enroll.status_code == 204
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        api_client.post("/api/v1/auth/login", json={"nickname": professor_nickname, "password": professor_password})
        enrolled = api_client.get(f"/api/v1/users/enrolled-users/{course_id}")
        assert enrolled.status_code == 200
        users = enrolled.json()
        assert any(u["nickname"] == student_nickname for u in users)

class TestUserIcon:
    @staticmethod
    @pytest.mark.integration
    def test_set_and_get_user_icon(student_client):
        profile = student_client.get("/api/v1/users/profile").json()
        user_id = profile["id"]
        files = {"icon_file": ("avatar.png", b"fake", "image/png")}
        set_icon = student_client.post("/api/v1/users/icon", files=files)
        assert set_icon.status_code == 204
        get_icon = student_client.get(f"/api/v1/users/{user_id}/icon")
        assert get_icon.status_code == 200
        assert get_icon.headers["content-type"] == "image/png"