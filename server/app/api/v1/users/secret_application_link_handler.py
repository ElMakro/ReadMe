from cryptography.fernet import Fernet

from server.config.settings import settings


class SecretApplicationLinkHandler:
    secret = settings.secret_link_key.get_secret_value()
    fernet = Fernet(secret)

    def get_encoded_link(self, link: str) -> str:
        return self.fernet.encrypt(link.encode()).decode()

    def get_decoded_link(self, encoded_link: str) -> str:
        return self.fernet.decrypt(encoded_link).decode()

    def verify_link(self, entered_link: str, encoded_true_link: str) -> bool:
        return entered_link == self.fernet.decrypt(encoded_true_link).decode()
