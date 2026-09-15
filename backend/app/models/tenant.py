from uuid import uuid4
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
