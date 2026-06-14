import uuid

import pytest


class TestAuthPositive:
    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "nickname, email, password",
        [
            (f"user_{uuid.uuid4().hex[:6]}", f"user_{uuid.uuid4().hex[:6]}@example.com", "StrongP@ss1"),
            (f"user_{uuid.uuid4().hex[:6]}", f"user_{uuid.uuid4().hex[:6]}@mail.ru", "12345678"),
            (f"user_{uuid.uuid4().hex[:6]}", f"user_{uuid.uuid4().hex[:6]}@yandex.ru", "qwerty123"),
            (f"user_{uuid.uuid4().hex[:6]}", f"user_{uuid.uuid4().hex[:6]}@gmail.com", "A" * 8),
            (f"user_{uuid.uuid4().hex[:6]}", f"user_{uuid.uuid4().hex[:6]}@test.org", "1" * 64),
            (f"user_{uuid.uuid4().hex[:6]}", f"user_{uuid.uuid4().hex[:6]}@test.com", "!@#$%^&*()_+"),
        ],
    )
    def test_register_success(api_client, nickname, email, password):
        reg = api_client.post("/api/v1/auth/reg", json={"nickname": nickname, "email": email, "password": password})
        assert reg.status_code == 201
        data = reg.json()
        assert data["nickname"] == nickname
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        login = api_client.post("/api/v1/auth/login", json={"nickname": nickname, "password": password})
        assert login.status_code == 200
        assert "Authorization" in login.cookies

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "nickname, password",
        [
            (f"user_{uuid.uuid4().hex[:6]}", "12345678"),
            (f"user_{uuid.uuid4().hex[:6]}", "StrongPassword123!"),
            (f"user_{uuid.uuid4().hex[:6]}", "Password"),
            (f"user_{uuid.uuid4().hex[:6]}", "1Pass2w345"),
            (f"user_{uuid.uuid4().hex[:6]}", "!!!!!!!!"),
        ],
    )
    def test_register_and_login_success(api_client, nickname, password):
        reg_result = api_client.post(
            "/api/v1/auth/reg", json={"nickname": nickname, "email": f"{nickname}@test.com", "password": password}
        )
        assert reg_result.status_code == 201

        login_result = api_client.post("/api/v1/auth/login", json={"nickname": nickname, "password": password})
        assert login_result.status_code == 200
        assert "Authorization" in login_result.cookies
        assert login_result.cookies["Authorization"].startswith("eyJ")

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "nickname, password",
        [
            (f"logout_user_{uuid.uuid4().hex[:6]}", "12345678"),
            (f"logout_user_{uuid.uuid4().hex[:6]}", "StrongPassword123!"),
            (f"logout_user_{uuid.uuid4().hex[:6]}", "Password"),
            (f"logout_user_{uuid.uuid4().hex[:6]}", "1Pass2w345"),
            (f"logout_user_{uuid.uuid4().hex[:6]}", "!!!!!!!!"),
        ],
    )
    def test_logout_clears_cookie(api_client, nickname, password):
        api_client.post(
            "/api/v1/auth/reg", json={"nickname": nickname, "email": f"{nickname}@t.com", "password": password}
        )
        api_client.post("/api/v1/auth/login", json={"nickname": nickname, "password": password})
        assert "Authorization" in api_client.cookies

        logout = api_client.get("/api/v1/auth/logout")
        assert logout.status_code == 200
        profile_after = api_client.get("/api/v1/users/profile")
        assert profile_after.status_code == 401


class TestAuthNegative:
    @staticmethod
    @pytest.mark.integration
    def test_register_missing_fields(api_client):
        result = api_client.post("/api/v1/auth/reg", json={"email": "test@test.com", "password": "12345678"})
        assert result.status_code == 422
        result = api_client.post("/api/v1/auth/reg", json={"nickname": "testuser", "password": "12345678"})
        assert result.status_code == 422
        result = api_client.post("/api/v1/auth/reg", json={"nickname": "testuser", "email": "test@test.com"})
        assert result.status_code == 422

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "email",
        [
            "invalid",
            "test@",
            "@example.com",
            "test@.com",
            "test@example",
            "test@example.",
            "test@example..com",
        ],
    )
    def test_register_invalid_email(api_client, email):
        nickname = f"user_{uuid.uuid4().hex[:6]}"
        result = api_client.post(
            "/api/v1/auth/reg", json={"nickname": nickname, "email": email, "password": "Strong123!"}
        )
        assert result.status_code == 422

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "nickname",
        [
            "a",
            "ab",
            "abc",
            "A" * 33,
            "user name",
            "user[name",
            "user]name",
            "user;name",
            "user:name",
            "user'name",
            'user"name',
            "user, name",
            "user/name",
            "user\\name",
            "user|name",
            "user`name",
            "user~name",
            "пользователь",
            "用户名",
            "😀user",
        ],
    )
    def test_register_invalid_nickname(api_client, nickname):
        result = api_client.post(
            "/api/v1/auth/reg",
            json={"nickname": nickname, "email": f"{uuid.uuid4().hex[:6]}@test.com", "password": "Strong123!"},
        )
        assert result.status_code == 422

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "password",
        [
            "short",
            "",
            "A" * 65,
            " ",
            "\t",
            "\n",
        ],
    )
    def test_register_invalid_password(api_client, password):
        nickname = f"user_{uuid.uuid4().hex[:6]}"
        result = api_client.post(
            "/api/v1/auth/reg", json={"nickname": nickname, "email": f"{nickname}@test.com", "password": password}
        )
        assert result.status_code == 422

    @staticmethod
    @pytest.mark.integration
    def test_register_duplicate_email(api_client):
        email = f"dupemail_{uuid.uuid4().hex[:6]}@test.com"
        nickname1 = f"user1_{uuid.uuid4().hex[:6]}"
        nickname2 = f"user2_{uuid.uuid4().hex[:6]}"
        password = "Strong123!"
        reg1 = api_client.post("/api/v1/auth/reg", json={"nickname": nickname1, "email": email, "password": password})
        assert reg1.status_code == 201
        reg2 = api_client.post("/api/v1/auth/reg", json={"nickname": nickname2, "email": email, "password": password})
        assert reg2.status_code == 409

    @staticmethod
    @pytest.mark.integration
    def test_register_special_characters_in_nickname_allowed(api_client):
        allowed_chars = ".-_!@#$%^&*()+=?<>"
        nickname = f"allowed{allowed_chars}{uuid.uuid4().hex[:4]}"
        nickname = nickname[:32]
        result = api_client.post(
            "/api/v1/auth/reg",
            json={"nickname": nickname, "email": f"{uuid.uuid4().hex[:6]}@test.com", "password": "Strong123!"},
        )
        assert result.status_code == 201, f"Nickname с разрешёнными символами должен проходить: {nickname}"

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "nickname, password",
        [
            (f"dup_{uuid.uuid4().hex[:6]}", "12345678"),
            (f"dup_{uuid.uuid4().hex[:6]}", "StrongPassword123!"),
            (f"dup_{uuid.uuid4().hex[:6]}", "Password"),
            (f"dup_{uuid.uuid4().hex[:6]}", "1Pass2w345"),
            (f"dup_{uuid.uuid4().hex[:6]}", "!!!!!!!!"),
        ],
    )
    def test_register_duplicate_nickname(api_client, nickname, password):
        api_client.post(
            "/api/v1/auth/reg", json={"nickname": nickname, "email": f"{nickname}1@t.com", "password": password}
        )
        result = api_client.post(
            "/api/v1/auth/reg", json={"nickname": nickname, "email": f"{nickname}2@t.com", "password": password}
        )
        assert result.status_code == 409

    @staticmethod
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "nickname, password",
        [
            (f"wrong_pass_{uuid.uuid4().hex[:6]}", "12345678"),
            (f"wrong_pass_{uuid.uuid4().hex[:6]}", "StrongPassword123!"),
            (f"wrong_pass_{uuid.uuid4().hex[:6]}", "Password"),
            (f"wrong_pass_{uuid.uuid4().hex[:6]}", "1Pass2w345"),
            (f"wrong_pass_{uuid.uuid4().hex[:6]}", "!!!!!!!!"),
        ],
    )
    def test_login_wrong_password(api_client, nickname, password):
        api_client.post(
            "/api/v1/auth/reg", json={"nickname": nickname, "email": f"{nickname}@t.com", "password": password}
        )
        result = api_client.post("/api/v1/auth/login", json={"nickname": nickname, "password": password + "error"})
        assert result.status_code == 401
