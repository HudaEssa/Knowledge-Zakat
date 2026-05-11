"""
Centralized application configuration.

All secrets (DB password, JWT signing key) are loaded from environment
variables. We deliberately do NOT provide insecure defaults for SECRET_KEY
or DATABASE_URL — the app refuses to start without them, which prevents
accidentally shipping a build that signs tokens with a placeholder.

Create a `.env` file at the project root:

    DATABASE_URL=postgresql://postgres:CHANGE_ME@localhost/knowledgeZakat
    JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(64))">
    JWT_ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=60
    CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
    SQL_ECHO=false
"""

import os
from functools import lru_cache
from typing import List

from dotenv import load_dotenv

load_dotenv()  # loads .env from cwd if present


class Settings:
    # ---- Database ---------------------------------------------------------
    DATABASE_URL: str = os.environ["DATABASE_URL"]  # KeyError on purpose

    # ---- JWT --------------------------------------------------------------
    # `os.environ[...]` (not `.get`) is intentional: if the key is missing
    # we want the app to crash on startup, not silently sign tokens with
    # an empty string.
    JWT_SECRET_KEY: str = os.environ["JWT_SECRET_KEY"]
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    # ---- CORS -------------------------------------------------------------
    @property
    def CORS_ORIGINS(self) -> List[str]:
        raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        return [o.strip() for o in raw.split(",") if o.strip()]

    # ---- File uploads -----------------------------------------------------
    # 5 MB is plenty for a profile picture and stops trivial DoS attempts
    # via giant uploads.
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(5 * 1024 * 1024)))
    ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp"}

    # ---- Misc -------------------------------------------------------------
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "false").lower() == "true"


@lru_cache
def _get_settings() -> Settings:
    return Settings()


settings = _get_settings()
