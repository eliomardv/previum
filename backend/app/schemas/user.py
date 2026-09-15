from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)
    tenant_id: str = Field(min_length=1, max_length=36)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    is_active: bool


class CurrentUserResponse(BaseModel):
    user: UserPublic
    tenant_id: str
