from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.worker import Worker


class WorkerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, worker_id: str, tenant_id: str):
        return self.db.scalar(select(Worker).where(
            Worker.id == worker_id, Worker.tenant_id == tenant_id))

    def list(self, tenant_id: str, company_id: str | None, offset: int, limit: int):
        query = select(Worker).where(Worker.tenant_id == tenant_id)
        if company_id is not None:
            query = query.where(Worker.company_id == company_id)
        return self.db.scalars(query.order_by(Worker.name, Worker.id)
                               .offset(offset).limit(limit)).all()

    def add(self, worker: Worker):
        self.db.add(worker)
