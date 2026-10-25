"""Single-origin ASGI entry point for the Flask app and both integrated tools."""
from __future__ import annotations

import importlib.util
import secrets
import sys
import types
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from a2wsgi import WSGIMiddleware

BASE_DIR = Path(__file__).resolve().parent
VET_BACKEND_DIR = BASE_DIR / "integrations" / "vet-app" / "backend"
SCHEME_BACKEND = BASE_DIR / "integrations" / "livestock-scheme-advisor" / "backend" / "app.py"

from app import app as flask_app  # noqa: E402

# Load the supplied backend in its own Python package namespace. This avoids
# collisions with the main Flask app's top-level `services` package.
vet_package = types.ModuleType("vet_integrated")
vet_package.__path__ = [str(VET_BACKEND_DIR)]
sys.modules[vet_package.__name__] = vet_package
from vet_integrated.main import app as veterinary_app  # noqa: E402
from vet_integrated.routes.veterinary import router as veterinary_router  # noqa: E402

spec = importlib.util.spec_from_file_location("kisansaathi_scheme_api", SCHEME_BACKEND)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load livestock scheme API from {SCHEME_BACKEND}")
scheme_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scheme_module
spec.loader.exec_module(scheme_module)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Mounted FastAPI apps do not receive lifespan events automatically.
    # Run the veterinary app's initializer explicitly (SQLite + bundled KML seed).
    async with veterinary_app.router.lifespan_context(veterinary_app):
        yield


application = FastAPI(
    title="Farm2Feed",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@application.middleware("http")
async def require_farmer_for_scheme_api(request, call_next):
    """Validate Flask's signed login cookie before allowing scheme API access."""
    if request.url.path == "/api/schemes" or request.url.path.startswith("/api/schemes/"):
        serializer = flask_app.session_interface.get_signing_serializer(flask_app)
        cookie_name = flask_app.config.get("SESSION_COOKIE_NAME", "session")
        cookie = request.cookies.get(cookie_name)
        try:
            max_age = int(flask_app.permanent_session_lifetime.total_seconds())
            session_data = (
                serializer.loads(cookie, max_age=max_age)
                if serializer and cookie
                else {}
            )
        except Exception:
            session_data = {}
        if not session_data.get("farmer_id"):
            return JSONResponse(
                {"detail": "Sign in with a farmer account to use the Livestock Scheme Advisor."},
                status_code=401,
            )
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            supplied = request.headers.get("x-csrf-token", "")
            expected = session_data.get("_csrf", "")
            if not supplied or not expected or not secrets.compare_digest(supplied, expected):
                return JSONResponse({"detail": "Missing or invalid CSRF token."}, status_code=403)
    return await call_next(request)


application.mount("/api/schemes", scheme_module.app)
application.include_router(veterinary_router)
application.mount("/", WSGIMiddleware(flask_app))

