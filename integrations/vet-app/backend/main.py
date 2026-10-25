"""
Maharashtra Veterinary & Animal Welfare Assistance
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .database import init_db, AsyncSessionLocal
from .routes.veterinary import router as vet_router
from sqlalchemy import func, select
from .models.veterinary import VeterinaryFacility
from .services.veterinary_service import import_kml_to_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on startup: create DB tables."""
    await init_db()
    print("[Startup] Database tables initialised.")
    async with AsyncSessionLocal() as session:
        # Reconcile bundled official source data on every startup. This also repairs
        # legacy rows imported with the old taluka parser and canonicalizes districts.
        result = await import_kml_to_db(session)
        print(f"[Startup] Reconciled {result['total_parsed']} veterinary facilities from bundled KML data.")
    yield
    print("[Shutdown] Bye.")


app = FastAPI(
    title="Maharashtra Veterinary Assistance API",
    description=(
        "Find nearby government veterinary facilities in Maharashtra. "
        "Data sourced from the Maharashtra Animal Husbandry Department (DAHD)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(vet_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Maharashtra Veterinary Assistance API",
        "status":  "running",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
