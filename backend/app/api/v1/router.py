from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, tenants, companies

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(health.router)
router.include_router(tenants.router)
router.include_router(companies.router)

from app.api.v1.endpoints import workers
router.include_router(workers.router)
