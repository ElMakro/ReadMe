import uuid
import pytest


class TestAuthPositive:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("nickname, password", [
        (f"user_{uuid.uuid4().hex[:6]}", "12345678"),
        (f"user_{uuid.uuid4().hex[:6]}", "StrongPassword123!"),
        (f"user_{uuid.uuid4().hex[:6]}", "Password"),
        (f"user_{uuid.uuid4().hex[:6]}", "1Pass2w345"),
        (f"user_{uuid.uuid4().hex[:6]}", "!!!!!!!!"),
    ])
    def test_register_and_login_success(api_client, nickname, password):
        reg_result = api_client.post("/api/v1/auth/reg", json={
            "nickname": nickname,
            "email": f"{nickname}@test.com",
            "password": password
        })
        assert reg_result.status_code == 201

        login_result = api_client.post("/api/v1/auth/login", json={
            "nickname": nickname,
            "password": password
        })
        assert login_result.status_code == 200
        assert "Authorization" in login_result.cookies
        assert login_result.cookies["Authorization"].startswith("eyJ")

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("nickname, password", [
        (f"logout_user_{uuid.uuid4().hex[:6]}", "12345678"),
        (f"logout_user_{uuid.uuid4().hex[:6]}", "StrongPassword123!"),
        (f"logout_user_{uuid.uuid4().hex[:6]}", "Password"),
        (f"logout_user_{uuid.uuid4().hex[:6]}", "1Pass2w345"),
        (f"logout_user_{uuid.uuid4().hex[:6]}", "!!!!!!!!"),
    ])
    def test_logout_clears_cookie(api_client, nickname, password):
        api_client.post("/api/v1/auth/reg", json={"nickname": nickname, "email": f"{nickname}@t.com", "password": password})
        api_client.post("/api/v1/auth/login", json={"nickname": nickname, "password": password})
        assert "Authorization" in api_client.cookies

        logout = api_client.get("/api/v1/auth/logout")
        assert logout.status_code == 200
        profile_after = api_client.get("/api/v1/users/profile")
        assert profile_after.status_code == 401


class TestAuthNegative:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("nickname, password", [
        (f"dup_{uuid.uuid4().hex[:6]}", "12345678"),
        (f"dup_{uuid.uuid4().hex[:6]}", "StrongPassword123!"),
        (f"dup_{uuid.uuid4().hex[:6]}", "Password"),
        (f"dup_{uuid.uuid4().hex[:6]}", "1Pass2w345"),
        (f"dup_{uuid.uuid4().hex[:6]}", "!!!!!!!!"),
    ])
    def test_register_duplicate_nickname(api_client, nickname, password):
        api_client.post("/api/v1/auth/reg", json={"nickname": nickname, "email": f"{nickname}1@t.com", "password": password})
        result = api_client.post("/api/v1/auth/reg", json={"nickname": nickname, "email": f"{nickname}2@t.com", "password": password})
        assert result.status_code == 409

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize("nickname, password", [
        (f"wrong_pass_{uuid.uuid4().hex[:6]}", "12345678"),
        (f"wrong_pass_{uuid.uuid4().hex[:6]}", "StrongPassword123!"),
        (f"wrong_pass_{uuid.uuid4().hex[:6]}", "Password"),
        (f"wrong_pass_{uuid.uuid4().hex[:6]}", "1Pass2w345"),
        (f"wrong_pass_{uuid.uuid4().hex[:6]}", "!!!!!!!!"),
    ])
    def test_login_wrong_password(api_client, nickname, password):
        api_client.post("/api/v1/auth/reg", json={"nickname": nickname, "email": f"{nickname}@t.com", "password": password})
        result = api_client.post("/api/v1/auth/login", json={"nickname": nickname, "password": password + "error"})
        assert result.status_code == 401