import uuid
import os
import pytest
from sqlalchemy import text

DEFAULT_SECRET_LINK = os.getenv("DEFAULT_SECRET_APPLICATION_LINK_PART", "submit_professor_application")

class TestProfessorApplication:
    @staticmethod
    @pytest.mark.integration
    def test_submit_application_success(api_client, _sync_sessionmaker):
        admin_nickname = f"admin_{uuid.uuid4().hex[:6]}"
        admin_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg", json={
            "email": f"{admin_nickname}@test.com",
            "nickname": admin_nickname,
            "password": admin_password
        })
        api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nickname,
            "password": admin_password
        })
        admin_profile = api_client.get("/api/v1/users/profile").json()
        admin_id = admin_profile["id"]
        with _sync_sessionmaker() as session:
            session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_id})
            session.commit()

        secret_link = f"test_link_{uuid.uuid4().hex[:6]}"
        set_result = api_client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link})
        assert set_result.status_code == 200

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname = f"student_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg", json={
            "email": f"{student_nickname}@test.com",
            "nickname": student_nickname,
            "password": student_password
        })
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
    def test_get_my_applications(api_client, _sync_sessionmaker):
        admin_nickname = f"admin_{uuid.uuid4().hex[:6]}"
        admin_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg", json={
            "email": f"{admin_nickname}@test.com",
            "nickname": admin_nickname,
            "password": admin_password
        })
        api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nickname,
            "password": admin_password
        })
        admin_profile = api_client.get("/api/v1/users/profile").json()
        admin_id = admin_profile["id"]
        with _sync_sessionmaker() as session:
            session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_id})
            session.commit()

        secret_link = f"test_link_{uuid.uuid4().hex[:6]}"
        set_result = api_client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link})
        assert set_result.status_code == 200

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname = f"student_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg", json={
            "email": f"{student_nickname}@test.com",
            "nickname": student_nickname,
            "password": student_password
        })
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
    def test_approve_application_changes_role(api_client, _sync_sessionmaker):
        admin_nickname = f"admin_{uuid.uuid4().hex[:6]}"
        admin_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg", json={
            "email": f"{admin_nickname}@test.com",
            "nickname": admin_nickname,
            "password": admin_password
        })
        api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nickname,
            "password": admin_password
        })
        admin_profile = api_client.get("/api/v1/users/profile").json()
        admin_id = admin_profile["id"]
        with _sync_sessionmaker() as session:
            session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_id})
            session.commit()

        secret_link = "test_approve_link"
        set_result = api_client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link})
        assert set_result.status_code == 200

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname = f"student_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg", json={
            "email": f"{student_nickname}@test.com",
            "nickname": student_nickname,
            "password": student_password
        })
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
    def test_change_user_role(api_client, _sync_sessionmaker):
        admin_nickname = f"admin_{uuid.uuid4().hex[:6]}"
        admin_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": admin_nickname, "email": f"{admin_nickname}@t.com", "password": admin_password})
        api_client.post("/api/v1/auth/login", json={"nickname": admin_nickname, "password": admin_password})
        admin_profile = api_client.get("/api/v1/users/profile").json()
        admin_id = admin_profile["id"]
        with _sync_sessionmaker() as session:
            session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_id})
            session.commit()
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname = f"student_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": student_nickname, "email": f"{student_nickname}@t.com", "password": student_password})
        api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})
        student_profile = api_client.get("/api/v1/users/profile").json()
        student_id = student_profile["id"]
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        api_client.post("/api/v1/auth/login", json={"nickname": admin_nickname, "password": admin_password})
        change = api_client.put("/api/v1/users/change-role", json={"id": student_id, "role": "admin"})
        assert change.status_code == 204

        with _sync_sessionmaker() as session:
            role = session.execute(text("SELECT role FROM users WHERE id = :uid"), {"uid": student_id}).scalar()
            assert role == "ADMIN"

    @staticmethod
    @pytest.mark.integration
    def test_delete_user(api_client, _sync_sessionmaker):
        admin_nickname = f"admin_{uuid.uuid4().hex[:6]}"
        admin_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": admin_nickname, "email": f"{admin_nickname}@t.com", "password": admin_password})
        api_client.post("/api/v1/auth/login", json={"nickname": admin_nickname, "password": admin_password})
        admin_profile = api_client.get("/api/v1/users/profile").json()
        admin_id = admin_profile["id"]
        with _sync_sessionmaker() as session:
            session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_id})
            session.commit()
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nickname = f"todelete_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": student_nickname, "email": f"{student_nickname}@t.com", "password": student_password})
        api_client.post("/api/v1/auth/login", json={"nickname": student_nickname, "password": student_password})
        student_profile = api_client.get("/api/v1/users/profile").json()
        student_id = student_profile["id"]
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        api_client.post("/api/v1/auth/login", json={"nickname": admin_nickname, "password": admin_password})
        delete = api_client.delete(f"/api/v1/users/delete-user/{student_id}")
        assert delete.status_code == 204
        with _sync_sessionmaker() as session:
            user = session.execute(text("SELECT * FROM users WHERE id = :uid"), {"uid": student_id}).fetchone()
            assert user is None