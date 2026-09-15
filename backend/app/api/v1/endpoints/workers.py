from fastapi import APIRouter, Query
from app.api.deps import CurrentUser, Db
from app.schemas.worker import WorkerCreate, WorkerPublic, WorkerUpdate
from app.services.worker_service import WorkerService

router = APIRouter(prefix="/workers", tags=["workers"])


@router.post("", response_model=WorkerPublic, status_code=201)
def create_worker(payload: WorkerCreate, db: Db, context: CurrentUser):
    return WorkerService(db).create(context.tenant_id, payload)


@router.get("", response_model=list[WorkerPublic])
def list_workers(db: Db, context: CurrentUser,
                 company_id: str | None = Query(default=None, min_length=1, max_length=36),
                 offset: int = Query(default=0, ge=0),
                 limit: int = Query(default=50, ge=1, le=100)):
    return WorkerService(db).list(context.tenant_id, company_id, offset, limit)


@router.get("/{worker_id}", response_model=WorkerPublic)
def get_worker(worker_id: str, db: Db, context: CurrentUser):
    return WorkerService(db).get(worker_id, context.tenant_id)


@router.patch("/{worker_id}", response_model=WorkerPublic)
def update_worker(worker_id: str, payload: WorkerUpdate, db: Db, context: CurrentUser):
    return WorkerService(db).update(worker_id, context.tenant_id, payload)
