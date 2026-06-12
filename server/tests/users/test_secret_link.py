import pytest
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException

from server.app.api.v1.users.secret_application_link_handler import SecretApplicationLinkHandler
from server.app.api.v1.users.users import UpdatedLinkContent
from server.app.common_dependencies.depends import get_new_link
from server.app.common_dependencies.secret_link_strategies import (
    CustomLinkStrategy,
    DefaultLinkStrategy,
    RandomLinkStrategy,
)
from server.config.settings import settings
from server.enums.updated_link_type import LinkType


@pytest.fixture
def mock_secret_key(monkeypatch):
    """Подменяет secret_link_key на валидный ключ Fernet."""
    test_key = Fernet.generate_key()
    monkeypatch.setattr(settings, "secret_link_key", test_key.decode())
    return test_key


@pytest.fixture
def handler(mock_secret_key):
    return SecretApplicationLinkHandler()


class TestSecretApplicationLinkHandler:
    def test_get_encoded_link_returns_different_string(self, handler):
        original = "https://example.com/apply/secret123"
        encoded = handler.get_encoded_link(original)
        assert encoded != original
        assert isinstance(encoded, str)

    def test_get_decoded_link_returns_original(self, handler):
        original = "some-link-data"
        encoded = handler.get_encoded_link(original)
        decoded = handler.get_decoded_link(encoded)
        assert decoded == original

    def test_verify_link_correct(self, handler):
        original = "very-secret-token"
        encoded = handler.get_encoded_link(original)
        assert handler.verify_link(original, encoded) is True

    def test_verify_link_incorrect(self, handler):
        original = "correct-token"
        encoded = handler.get_encoded_link(original)
        wrong = "wrong-token"
        assert handler.verify_link(wrong, encoded) is False

    def test_empty_string(self, handler):
        original = ""
        encoded = handler.get_encoded_link(original)
        decoded = handler.get_decoded_link(encoded)
        assert decoded == original
        assert handler.verify_link(original, encoded) is True

    def test_long_string(self, handler):
        original = "x" * 10000
        encoded = handler.get_encoded_link(original)
        decoded = handler.get_decoded_link(encoded)
        assert decoded == original

    def test_special_characters(self, handler):
        original = "привет мир! @#$%^&*()_+={}[]|\\;:'\",.<>/?"
        encoded = handler.get_encoded_link(original)
        decoded = handler.get_decoded_link(encoded)
        assert decoded == original

    def test_decoding_invalid_token_raises_exception(self, handler):
        invalid_encoded = "invalid-fernet-token"
        with pytest.raises(InvalidToken):
            handler.get_decoded_link(invalid_encoded)

    def test_verify_link_invalid_token_raises_exception(self, handler):
        invalid_encoded = "garbage"
        with pytest.raises(InvalidToken):
            handler.verify_link("anything", invalid_encoded)


class TestStrategies:
    def test_custom_link_strategy_returns_given_link(self):
        link = "my-custom-link"
        strategy = CustomLinkStrategy(link)
        assert strategy.new_link == link

    def test_random_link_strategy_returns_non_empty_string(self):
        strategy = RandomLinkStrategy()
        link = strategy.new_link
        assert isinstance(link, str)
        assert len(link) > 0
        assert all(c.isalnum() or c in "-_" for c in link)

    def test_default_link_strategy_uses_settings(self, monkeypatch):
        default_part = "default_secret_part_123"
        monkeypatch.setattr(settings, "default_secret_application_link_part", default_part)
        strategy = DefaultLinkStrategy()
        assert strategy.new_link == default_part


class TestGetNewLink:
    def test_default_type_returns_default_strategy(self):
        content = UpdatedLinkContent(type=LinkType.DEFAULT, content=None)
        result = get_new_link(content)
        assert isinstance(result, DefaultLinkStrategy)

    def test_random_type_returns_random_strategy(self):
        content = UpdatedLinkContent(type=LinkType.RANDOM, content=None)
        result = get_new_link(content)
        assert isinstance(result, RandomLinkStrategy)

    def test_custom_type_with_valid_content_returns_custom_strategy(self):
        content = UpdatedLinkContent(type=LinkType.CUSTOM, content="my-link")
        result = get_new_link(content)
        assert isinstance(result, CustomLinkStrategy)
        assert result.new_link == "my-link"

    def test_custom_type_with_empty_content_raises_422(self):
        content = UpdatedLinkContent(type=LinkType.CUSTOM, content="")
        with pytest.raises(HTTPException) as exc:
            get_new_link(content)
        assert exc.value.status_code == 422
        assert "Ссылка не задана" in str(exc.value.detail)

    def test_custom_type_with_whitespace_only_content_raises_422(self):
        content = UpdatedLinkContent(type=LinkType.CUSTOM, content="   ")
        with pytest.raises(HTTPException) as exc:
            get_new_link(content)
        assert exc.value.status_code == 422

    def test_custom_type_with_none_content_raises_422(self):
        content = UpdatedLinkContent(type=LinkType.CUSTOM, content=None)
        with pytest.raises(HTTPException) as exc:
            get_new_link(content)
        assert exc.value.status_code == 422
