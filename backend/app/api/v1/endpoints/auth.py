from fastapi import APIRouter, Response
from sqlalchemy import select
from app.api.deps import CurrentUser, Db, active_membership, unauthorized
from app.core.config import settings
from app.core.security import DUMMY_HASH, create_access_token, verify_password
from app.models.user import User
from app.schemas.user import CurrentUserResponse, LoginRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Db, response: Response):
    user = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    valid = verify_password(payload.password, user.password_hash if user else DUMMY_HASH)
    if not valid or user is None or not active_membership(db, user, payload.tenant_id):
        raise unauthorized()
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return TokenResponse(
        access_token=create_access_token(user.id, payload.tenant_id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=CurrentUserResponse)
def me(context: CurrentUser):
    return CurrentUserResponse(user=UserPublic.model_validate(context.user), tenant_id=context.tenant_id)
