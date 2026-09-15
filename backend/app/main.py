from fastapi import FastAPI
from app.api.v1.router import router

app = FastAPI(title="Previum")
from app.api.error_handlers import business_error_handler
from app.core.exceptions import BusinessError

app.add_exception_handler(BusinessError, business_error_handler)
app.include_router(router)

# The optional compiled SPA uses hash routing, preserving API 404 responses.
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = Path(__file__).resolve().parents[1] / "frontend_dist"
if (frontend_dist / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    def frontend():
        return FileResponse(frontend_dist / "index.html", headers={"Cache-Control": "no-cache"})
