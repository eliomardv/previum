from sqlalchemy.orm import Session
from app.core.exceptions import CompanyNotFound, WorkerNotFound
from app.models.worker import Worker
from app.repositories.company_repository import CompanyRepository
from app.repositories.worker_repository import WorkerRepository
from app.schemas.worker import WorkerCreate, WorkerPublic, WorkerUpdate


class WorkerService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = WorkerRepository(db)
        self.companies = CompanyRepository(db)

    def _company(self, company_id: str, tenant_id: str):
        if self.companies.get(company_id, tenant_id) is None:
            raise CompanyNotFound()

    def get(self, worker_id: str, tenant_id: str):
        worker = self.repository.get(worker_id, tenant_id)
        if worker is None:
            raise WorkerNotFound()
        return worker

    def list(self, tenant_id: str, company_id: str | None, offset: int, limit: int):
        if company_id is not None:
            self._company(company_id, tenant_id)
        return self.repository.list(tenant_id, company_id, offset, limit)

    def _save(self, worker: Worker):
        self.db.flush()
        result = WorkerPublic.model_validate(worker)
        self.db.commit()
        return result

    def create(self, tenant_id: str, payload: WorkerCreate):
        try:
            self._company(payload.company_id, tenant_id)
            worker = Worker(tenant_id=tenant_id, **payload.model_dump())
            self.repository.add(worker)
            return self._save(worker)
        except Exception:
            self.db.rollback()
            raise

    def update(self, worker_id: str, tenant_id: str, payload: WorkerUpdate):
        try:
            worker = self.get(worker_id, tenant_id)
            self._company(payload.company_id or worker.company_id, tenant_id)
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(worker, field, value)
            return self._save(worker)
        except Exception:
            self.db.rollback()
            raise
