import datetime
import uuid
from unittest.mock import patch

import jwt
import pytest

from server.app.api.v1.auth.auth_handler import AuthHandler
from server.config.settings import settings

pytestmark = pytest.mark.asyncio


class TestGetHashedPassword:
    async def test_returns_different_hash_for_same_password(self):
        handler = AuthHandler()
        password = "my_secret_password"
        hash1 = await handler.get_hashed_password(password)
        hash2 = await handler.get_hashed_password(password)
        assert hash1 != hash2
        assert hash1.startswith("$2b$")
        assert hash2.startswith("$2b$")

    async def test_hash_is_not_equal_to_plain(self):
        handler = AuthHandler()
        password = "simple"
        hashed = await handler.get_hashed_password(password)
        assert hashed != password


class TestVerifyPassword:
    async def test_verify_correct_password(self):
        handler = AuthHandler()
        password = "correct"
        hashed = await handler.get_hashed_password(password)
        assert await handler.verify_password(password, hashed) is True

    async def test_verify_wrong_password(self):
        handler = AuthHandler()
        password = "realpass"
        wrong = "wrongpass"
        hashed = await handler.get_hashed_password(password)
        assert await handler.verify_password(wrong, hashed) is False


class TestCreateToken:
    async def test_returns_token_and_session_id(self):
        handler = AuthHandler()
        user_id = uuid.uuid4()
        token, session_id = await handler.create_token(user_id)

        assert isinstance(token, str)
        assert isinstance(session_id, str)

        payload = jwt.decode(
            token,
            key=handler.secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        assert payload["user_id"] == str(user_id)
        assert payload["session_id"] == session_id
        assert "exp" in payload

        now = datetime.datetime.now(datetime.UTC)
        exp = datetime.datetime.fromtimestamp(payload["exp"], tz=datetime.UTC)
        assert exp > now

    async def test_token_expiration_uses_settings(self):
        mock_expire = 12345
        with patch.object(settings, "token_expire", mock_expire):
            handler = AuthHandler()
            user_id = uuid.uuid4()
            token, _ = await handler.create_token(user_id)
            payload = jwt.decode(token, key=handler.secret, algorithms=["HS256"])
            now = datetime.datetime.now(datetime.UTC)
            exp_datetime = datetime.datetime.fromtimestamp(payload["exp"], tz=datetime.UTC)
            diff = (exp_datetime - now).total_seconds()
            assert abs(diff - mock_expire) < 2


class TestDecodeToken:
    async def test_decode_valid_token(self):
        handler = AuthHandler()
        user_id = uuid.uuid4()
        token, session_id = await handler.create_token(user_id)
        payload = await handler.decode_token(token)
        assert payload["user_id"] == str(user_id)
        assert payload["session_id"] == session_id
        assert "exp" in payload

    async def test_decode_expired_token_raises_expired_signature_error(self):
        handler = AuthHandler()
        user_id = uuid.uuid4()
        expire = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=10)
        payload = {
            "user_id": str(user_id),
            "session_id": "sess",
            "exp": expire
        }
        expired_token = jwt.encode(payload, handler.secret, algorithm="HS256")
        with pytest.raises(jwt.exceptions.ExpiredSignatureError):
            await handler.decode_token(expired_token)

    async def test_decode_invalid_token_raises_decode_error(self):
        handler = AuthHandler()
        invalid_token = "this.is.not.a.valid.token"
        with pytest.raises(jwt.exceptions.DecodeError):
            await handler.decode_token(invalid_token)

    async def test_decode_token_with_wrong_secret_raises_invalid_signature_error(self):
        other_secret = "different_secret".rjust(32)
        handler = AuthHandler()
        payload = {"user_id": str(uuid.uuid4()),
                   "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)}
        token_with_other_secret = jwt.encode(payload, other_secret, algorithm="HS256")
        with pytest.raises(jwt.exceptions.InvalidSignatureError):
            await handler.decode_token(token_with_other_secret)
