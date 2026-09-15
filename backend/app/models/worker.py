from uuid import uuid4
from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class Worker(Base):
    __tablename__ = "workers"
    __table_args__ = (Index("ix_workers_tenant_company", "tenant_id", "company_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String(200))
    registration: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
