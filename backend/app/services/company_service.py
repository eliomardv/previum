from sqlalchemy.orm import Session
from app.core.exceptions import CompanyNotFound
from app.models.company import Company
from app.repositories.company_repository import CompanyRepository
from app.schemas.company import CompanyCreate, CompanyPublic, CompanyUpdate


class CompanyService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CompanyRepository(db)

    def get(self, company_id: str, tenant_id: str):
        company = self.repository.get(company_id, tenant_id)
        if company is None:
            raise CompanyNotFound()
        return company

    def list(self, tenant_id: str, offset: int, limit: int):
        return self.repository.list(tenant_id, offset, limit)

    def _save(self, company: Company) -> CompanyPublic:
        # Materialize the response before commit to avoid a post-commit refresh.
        self.db.flush()
        result = CompanyPublic.model_validate(company)
        self.db.commit()
        return result

    def create(self, tenant_id: str, payload: CompanyCreate):
        try:
            company = Company(tenant_id=tenant_id, **payload.model_dump())
            self.repository.add(company)
            return self._save(company)
        except Exception:
            self.db.rollback()
            raise

    def update(self, company_id: str, tenant_id: str, payload: CompanyUpdate):
        try:
            company = self.get(company_id, tenant_id)
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(company, field, value)
            return self._save(company)
        except Exception:
            self.db.rollback()
            raise
