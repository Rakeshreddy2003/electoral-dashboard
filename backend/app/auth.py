from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.models import Role

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(email: str, role: Role) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": email, "role": role.value, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


PII_FIELDS = ("contact_name", "contact_phone_1", "contact_phone_2")


def strip_pii(record: dict, role: Role) -> dict:
    """
    Removes PII fields for any role other than admin. This must be applied
    server-side on every response payload that can contain respondent
    contact details -- the frontend never receives these fields for
    analyst/viewer roles, it isn't just hidden in the UI.
    """
    if role == Role.admin:
        return record
    return {k: v for k, v in record.items() if k not in PII_FIELDS}
