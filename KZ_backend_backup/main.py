"""
Knowledge Zakat — FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from database import init_db
from routers import users, sessions, admin, auth

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown hook. We replace the legacy module-level
    `metadata.create_all(...)` call with a lifespan event so the
    database connection is opened *after* settings are validated.
    """
    init_db()
    yield


app = FastAPI(
    title="Knowledge Zakat API",
    version="1.0.0",
    description="منصة Knowledge Zakat للتعليم — Backend API",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Rate limiting (SlowAPI)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# Origins come from settings (env-driven), not from a hard-coded list.
# We keep allow_credentials=True because the Svelte client may send the
# Authorization header; that combination requires explicit origins
# (wildcard "*" is rejected by browsers when credentials are on).
#
# BUG FIX: removed the duplicate CORSMiddleware block. Two add_middleware
# calls were stacking, and the second one (wide-open methods/headers)
# was silently overriding the first one. Now there is exactly one CORS
# layer driven entirely by CORS_ORIGINS from the .env file.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
# Order matters only for documentation grouping. The actual URL paths
# stay identical to the previous version so the Svelte frontend keeps
# working untouched.
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(sessions.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
def root():
    """Simple health probe so deploy tooling can verify the app booted."""
    return {"message": "Knowledge Zakat API is running correctly!"}


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
# These directories are created on first run by the upload routes;
# mounting them here exposes saved cover images and profile uploads
# back to the client.
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/pics", StaticFiles(directory="pics"), name="pics")