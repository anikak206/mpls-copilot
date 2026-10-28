"""FastAPI entry point for the Air-Gapped Predictive Copilot for Secure MPLS Operations."""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.exc import DBAPIError, IntegrityError  # noqa: E402

from app.bootstrap import bootstrap  # noqa: E402
from app.config import settings  # noqa: E402
from app.database import engine  # noqa: E402
from app.routers import actions, auth, dblab, deliverables, devices, incidents, predictions, reports, telemetry, users  # noqa: E402

logger = logging.getLogger("mpls")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    bootstrap()
    yield


app = FastAPI(title="Air-Gapped Predictive Copilot for Secure MPLS Operations", version="1.0.0",
              description="Secure, locally deployable MPLS operations API (MySQL + local ML).",
              lifespan=lifespan, docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json")

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
                   allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"],
                   expose_headers=["Content-Disposition"])

for module in (auth, users, devices, telemetry, incidents, predictions, actions, reports, dblab, deliverables):
    app.include_router(module.router)


@app.exception_handler(IntegrityError)
async def integrity_handler(_req: Request, exc: IntegrityError):
    code = exc.orig.args[0] if exc.orig and exc.orig.args else None
    message = {1062: "Duplicate value violates a unique constraint",
               1451: "Record is referenced by other records",
               1452: "Referenced record does not exist"}.get(code, "Operation violates a database constraint")
    return JSONResponse(status_code=409, content={"detail": message})


@app.exception_handler(DBAPIError)
async def dbapi_handler(_req: Request, exc: DBAPIError):
    code = exc.orig.args[0] if exc.orig and exc.orig.args else None
    if code in (3819, 4025):
        return JSONResponse(status_code=422, content={"detail": "Value violates a database CHECK constraint"})
    if code == 1644:
        return JSONResponse(status_code=400, content={"detail": str(exc.orig.args[1])})
    logger.exception("Database error")
    return JSONResponse(status_code=500, content={"detail": "Database error"})


@app.get("/api/health", tags=["Health"])
def health():
    with engine.connect() as conn:
        version = conn.execute(text("SELECT VERSION()")).scalar()
    return {"status": "ok", "database": "MySQL-compatible", "server_version": version}
