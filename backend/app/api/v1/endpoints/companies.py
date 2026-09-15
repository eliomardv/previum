from fastapi import APIRouter, Query
from app.api.deps import CurrentUser, Db
from app.schemas.company import CompanyCreate, CompanyPublic, CompanyUpdate
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyPublic, status_code=201)
def create_company(payload: CompanyCreate, db: Db, context: CurrentUser):
    return CompanyService(db).create(context.tenant_id, payload)


@router.get("", response_model=list[CompanyPublic])
def list_companies(db: Db, context: CurrentUser,
                   offset: int = Query(default=0, ge=0),
                   limit: int = Query(default=50, ge=1, le=100)):
    return CompanyService(db).list(context.tenant_id, offset, limit)


@router.get("/{company_id}", response_model=CompanyPublic)
def get_company(company_id: str, db: Db, context: CurrentUser):
    return CompanyService(db).get(company_id, context.tenant_id)


@router.patch("/{company_id}", response_model=CompanyPublic)
def update_company(company_id: str, payload: CompanyUpdate, db: Db, context: CurrentUser):
    return CompanyService(db).update(company_id, context.tenant_id, payload)
