import secrets
from abc import ABC, abstractmethod

from server.config.settings import settings


class UpdatedLinkStrategy(ABC):
    @property
    @abstractmethod
    def new_link(self) -> str:
        pass


class RandomLinkStrategy(UpdatedLinkStrategy):
    @property
    def new_link(self) -> str:
        return secrets.token_urlsafe(32)


class CustomLinkStrategy(UpdatedLinkStrategy):
    def __init__(self, new_link: str):
        self.__new_link = new_link

    @property
    def new_link(self) -> str:
        return self.__new_link


class DefaultLinkStrategy(UpdatedLinkStrategy):
    def __init__(self):
        self.__default_link = settings.default_secret_application_link_part

    @property
    def new_link(self) -> str:
        return self.__default_link
