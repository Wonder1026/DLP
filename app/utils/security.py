import hashlib


def hash_password(password: str) -> str:
    """Простое хеширование пароля через SHA-256 (для прототипа)"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return hash_password(plain_password) == hashed_password