from fastapi import APIRouter, HTTPException
from app.api.deps import CurrentUser, Db
from app.models.tenant import Tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/{tenant_id}")
def get_tenant(tenant_id: str, context: CurrentUser, db: Db):
    if tenant_id != context.tenant_id:
        raise HTTPException(404, "Tenant não encontrado")
    tenant = db.get(Tenant, context.tenant_id)
    return {"id": tenant.id, "name": tenant.name}
