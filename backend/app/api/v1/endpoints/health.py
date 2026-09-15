from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.api.deps import Db

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready", responses={503: {"description": "Banco indisponível"}})
def ready(db: Db):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ok"}
