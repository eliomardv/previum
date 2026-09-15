from dataclasses import dataclass
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import Membership, User
from app.models.tenant import Tenant


def get_db():
    with SessionLocal() as db:
        yield db


Db = Annotated[Session, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)


def unauthorized():
    return HTTPException(401, "Credenciais inválidas", headers={"WWW-Authenticate": "Bearer"})


def active_membership(db: Session, user: User, tenant_id: str) -> bool:
    membership = db.get(Membership, (user.id, tenant_id))
    tenant = db.get(Tenant, tenant_id)
    return bool(user.is_active and membership and membership.is_active and tenant and tenant.is_active)


@dataclass
class AuthContext:
    user: User
    tenant_id: str


def get_current_user(
    db: Db,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthContext:
    if credentials is None:
        raise unauthorized()
    try:
        claims = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise unauthorized() from None
    user = db.get(User, claims["sub"])
    if user is None or not active_membership(db, user, claims["tenant_id"]):
        raise unauthorized()
    return AuthContext(user, claims["tenant_id"])


CurrentUser = Annotated[AuthContext, Depends(get_current_user)]
