from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from pwdlib import PasswordHash
from app.core.config import settings

password_hasher = PasswordHash.recommended()
DUMMY_HASH = password_hasher.hash("unused-dummy-password")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id: str, tenant_id: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": user_id, "tenant_id": tenant_id,
        "iat": now, "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": str(uuid4()), "iss": "previum", "aud": "previum-api",
    }, settings.JWT_SECRET_KEY.get_secret_value(), algorithm="HS256")


def decode_access_token(token: str) -> dict:
    claims = jwt.decode(
        token, settings.JWT_SECRET_KEY.get_secret_value(), algorithms=["HS256"],
        issuer="previum", audience="previum-api",
        options={"require": ["sub", "tenant_id", "iat", "exp", "jti", "iss", "aud"]},
    )
    for key in ("sub", "tenant_id", "jti"):
        if not isinstance(claims[key], str) or not claims[key]:
            raise jwt.InvalidTokenError("Invalid identity claim")
    return claims
