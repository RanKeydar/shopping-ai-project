from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)