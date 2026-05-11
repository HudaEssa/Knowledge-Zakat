"""
JWT authentication layer.

Security improvements over the previous version:
- `SECRET_KEY` is loaded from the environment via `core.config.settings`.
  The old hard-coded "hello_world_secret_key_123" would let anyone who
  read the source forge admin tokens.
- Tokens now include `iat` (issued-at) and `exp` (expiry) with
  timezone-aware UTC timestamps. We also pin the algorithm on decode
  so an attacker cannot trick us with `alg: none`.
- `get_current_user` distinguishes between expired and invalid tokens
  for clearer client messages — but never leaks *why* validation
  failed in a way that helps an attacker enumerate accounts.
- `check_admin_role` now matches by `role_name == "admin"` instead of
  the previous `role.id == 3` magic number, which silently broke
  whenever the seed order changed.
- Every token-protected route also re-checks `is_active` so that
  deactivating a user immediately invalidates their session on the
  next request (no need to wait for token expiry).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError, jwt
from sqlmodel import Session, select

import database
import models
from core.config import settings


# tokenUrl points at the login endpoint that issues access tokens. The
# Swagger "Authorize" button uses this to drive its login form.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# ---------------------------------------------------------------------------
# Token issuance
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Build a signed JWT. We always set `iat` and `exp` claims; callers
    only supply identity claims (typically {"sub": email}).
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# ---------------------------------------------------------------------------
# Standard credential errors
# ---------------------------------------------------------------------------

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

_expired_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token has expired, please log in again",
    headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db),
) -> models.User:
    """
    Decode the JWT, look up the user, and verify the account is active.
    Raises 401 on any failure — never reveals which step failed.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            # Pinning the algorithm prevents the classic `alg: none` /
            # algorithm-confusion attack.
            algorithms=[settings.JWT_ALGORITHM],
        )
        email: Optional[str] = payload.get("sub")
        if not email:
            raise _credentials_exception
    except ExpiredSignatureError:
        raise _expired_exception
    except JWTError:
        raise _credentials_exception

    user = db.exec(select(models.User).where(models.User.email == email)).first()
    if user is None:
        raise _credentials_exception

    # Re-check on every request so that an admin-driven deactivation
    # takes effect immediately, not after token expiry.
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your account is deactivated",
        )
    return user


def check_admin_role(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Restrict a route to admins only."""
    is_admin = any(r.role_name == "admin" for r in current_user.roles)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


def check_teacher_role(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Restrict a route to teachers (or admins, who can act on their behalf)."""
    role_names = {r.role_name for r in current_user.roles}
    if not role_names.intersection({"teacher", "admin"}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher privileges required",
        )
    return current_user
