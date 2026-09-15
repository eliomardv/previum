from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import BusinessError, CompanyNotFound, WorkerNotFound


async def business_error_handler(request: Request, exc: BusinessError):
    if isinstance(exc, WorkerNotFound):
        return JSONResponse(status_code=404, content={"detail": "Trabalhador não encontrado"})
    if isinstance(exc, CompanyNotFound):
        return JSONResponse(status_code=404, content={"detail": "Empresa não encontrada"})
    return JSONResponse(status_code=400, content={"detail": "Operação inválida"})
