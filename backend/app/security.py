from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

password_hash = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return password_hash.verify(password, hashed_password)