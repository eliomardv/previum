from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.company import Company


class CompanyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, company_id: str, tenant_id: str) -> Company | None:
        return self.db.scalar(select(Company).where(
            Company.id == company_id, Company.tenant_id == tenant_id))

    def list(self, tenant_id: str, offset: int, limit: int):
        return self.db.scalars(select(Company).where(Company.tenant_id == tenant_id)
                               .order_by(Company.name, Company.id)
                               .offset(offset).limit(limit)).all()

    def add(self, company: Company):
        self.db.add(company)
