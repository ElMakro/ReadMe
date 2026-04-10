from passlib.context import CryptContext
from config.settings import settings


class AuthHandler:
    secret = settings.secret_key.get_secret_value()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def get_hashed_password(self, password: str) -> str:
        return self.pwd_context.hash(password)
