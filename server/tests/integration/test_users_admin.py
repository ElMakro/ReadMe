import uuid
import os
from sqlalchemy import text

DEFAULT_SECRET_LINK = os.getenv("DEFAULT_SECRET_APPLICATION_LINK_PART", "submit_professor_application")

class TestProfessorApplication:
    @staticmethod
    def test_submit_application_success(api_client, _sync_sessionmaker):
        admin_nick = f"admin_{uuid.uuid4().hex[:6]}"
        admin_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg", json={
            "email": f"{admin_nick}@test.com",
            "nickname": admin_nick,
            "password": admin_password
        })
        api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nick,
            "password": admin_password
        })
        admin_profile = api_client.get("/api/v1/users/profile").json()
        admin_id = admin_profile["id"]
        with _sync_sessionmaker() as session:
            session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_id})
            session.commit()

        secret_link = f"test_link_{uuid.uuid4().hex[:6]}"
        set_res = api_client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link})
        assert set_res.status_code == 200

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nick = f"student_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg", json={
            "email": f"{student_nick}@test.com",
            "nickname": student_nick,
            "password": student_password
        })
        api_client.post("/api/v1/auth/login", json={
            "nickname": student_nick,
            "password": student_password
        })

        res = api_client.post(f"/api/v1/users/submit-professor-application/{secret_link}", json={
            "name": "Иван",
            "surname": "Иванов"
        })
        assert res.status_code == 201
        assert "id" in res.json()

    @staticmethod
    def test_get_my_applications(api_client, _sync_sessionmaker):
        admin_nick = f"admin_{uuid.uuid4().hex[:6]}"
        admin_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg", json={
            "email": f"{admin_nick}@test.com",
            "nickname": admin_nick,
            "password": admin_password
        })
        api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nick,
            "password": admin_password
        })
        admin_profile = api_client.get("/api/v1/users/profile").json()
        admin_id = admin_profile["id"]
        with _sync_sessionmaker() as session:
            session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_id})
            session.commit()

        secret_link = f"test_link_{uuid.uuid4().hex[:6]}"
        set_res = api_client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link})
        assert set_res.status_code == 200

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nick = f"student_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg", json={
            "email": f"{student_nick}@test.com",
            "nickname": student_nick,
            "password": student_password
        })
        api_client.post("/api/v1/auth/login", json={
            "nickname": student_nick,
            "password": student_password
        })

        submit_res = api_client.post(f"/api/v1/users/submit-professor-application/{secret_link}", json={
            "name": "Пётр", "surname": "Петров"
        })
        assert submit_res.status_code == 201

        res = api_client.get("/api/v1/users/get-my-applications")
        assert res.status_code == 200
        applications = res.json()
        assert len(applications) > 0
        found = any(app["application_id"] == submit_res.json()["id"] for app in applications)
        assert found, "Созданная заявка не найдена в списке"

    @staticmethod
    def test_approve_application_changes_role(api_client, _sync_sessionmaker):
        admin_nick = f"admin_{uuid.uuid4().hex[:6]}"
        admin_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg", json={
            "email": f"{admin_nick}@test.com",
            "nickname": admin_nick,
            "password": admin_password
        })
        api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nick,
            "password": admin_password
        })
        admin_profile = api_client.get("/api/v1/users/profile").json()
        admin_id = admin_profile["id"]
        with _sync_sessionmaker() as session:
            session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_id})
            session.commit()

        secret_link = "test_approve_link"
        set_res = api_client.post("/api/v1/users/set-application-link", json={"type": "custom", "content": secret_link})
        assert set_res.status_code == 200

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nick = f"student_{uuid.uuid4().hex[:6]}"
        student_password = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg", json={
            "email": f"{student_nick}@test.com",
            "nickname": student_nick,
            "password": student_password
        })
        api_client.post("/api/v1/auth/login", json={
            "nickname": student_nick,
            "password": student_password
        })
        student_profile = api_client.get("/api/v1/users/profile").json()
        student_id = student_profile["id"]

        submit_res = api_client.post(f"/api/v1/users/submit-professor-application/{secret_link}", json={
            "name": "Сергей",
            "surname": "Сергеев"
        })
        assert submit_res.status_code == 201
        app_id = submit_res.json()["id"]

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        api_client.post("/api/v1/auth/login", json={
            "nickname": admin_nick,
            "password": admin_password
        })
        approve_res = api_client.put("/api/v1/users/change-application-status", json={
            "application_id": app_id,
            "user_id": student_id,
            "status": "approved"
        })
        assert approve_res.status_code in [200, 204]

        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        login_res = api_client.post("/api/v1/auth/login", json={
            "nickname": student_nick,
            "password": student_password
        })
        assert login_res.status_code == 200
        new_profile = api_client.get("/api/v1/users/profile").json()
        assert new_profile["role"] == "professor"

class TestAdminUserManagement:
    @staticmethod
    def test_get_all_users(admin_client):
        res = admin_client.get("/api/v1/users/all")
        assert res.status_code == 200
        assert len(res.json()) >= 1

    @staticmethod
    def test_change_user_role(api_client, _sync_sessionmaker):
        admin_nick = f"admin_{uuid.uuid4().hex[:6]}"
        admin_pass = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": admin_nick, "email": f"{admin_nick}@t.com", "password": admin_pass})
        api_client.post("/api/v1/auth/login", json={"nickname": admin_nick, "password": admin_pass})
        admin_profile = api_client.get("/api/v1/users/profile").json()
        admin_id = admin_profile["id"]
        with _sync_sessionmaker() as session:
            session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_id})
            session.commit()
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nick = f"student_{uuid.uuid4().hex[:6]}"
        student_pass = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": student_nick, "email": f"{student_nick}@t.com", "password": student_pass})
        api_client.post("/api/v1/auth/login", json={"nickname": student_nick, "password": student_pass})
        student_profile = api_client.get("/api/v1/users/profile").json()
        student_id = student_profile["id"]
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        api_client.post("/api/v1/auth/login", json={"nickname": admin_nick, "password": admin_pass})
        change = api_client.put("/api/v1/users/change-role", json={"id": student_id, "role": "admin"})
        assert change.status_code == 204

        with _sync_sessionmaker() as session:
            role = session.execute(text("SELECT role FROM users WHERE id = :uid"), {"uid": student_id}).scalar()
            assert role == "ADMIN"

    @staticmethod
    def test_delete_user(api_client, _sync_sessionmaker):
        admin_nick = f"admin_{uuid.uuid4().hex[:6]}"
        admin_pass = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": admin_nick, "email": f"{admin_nick}@t.com", "password": admin_pass})
        api_client.post("/api/v1/auth/login", json={"nickname": admin_nick, "password": admin_pass})
        admin_profile = api_client.get("/api/v1/users/profile").json()
        admin_id = admin_profile["id"]
        with _sync_sessionmaker() as session:
            session.execute(text("UPDATE users SET role = 'ADMIN' WHERE id = :uid"), {"uid": admin_id})
            session.commit()
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        student_nick = f"todelete_{uuid.uuid4().hex[:6]}"
        student_pass = "StrongPassword123!"
        api_client.post("/api/v1/auth/reg",
                        json={"nickname": student_nick, "email": f"{student_nick}@t.com", "password": student_pass})
        api_client.post("/api/v1/auth/login", json={"nickname": student_nick, "password": student_pass})
        student_profile = api_client.get("/api/v1/users/profile").json()
        student_id = student_profile["id"]
        api_client.get("/api/v1/auth/logout")
        api_client.cookies.clear()

        api_client.post("/api/v1/auth/login", json={"nickname": admin_nick, "password": admin_pass})
        delete = api_client.delete(f"/api/v1/users/delete-user/{student_id}")
        assert delete.status_code == 204
        with _sync_sessionmaker() as session:
            user = session.execute(text("SELECT * FROM users WHERE id = :uid"), {"uid": student_id}).fetchone()
            assert user is None