"""
Authentication & utility helpers.

Security improvements over the previous version:
- `bcrypt` rounds are explicitly set (12) instead of relying on passlib's
  default — this is the OWASP-recommended floor as of 2024.
- Password hashing/verification still uses passlib's `CryptContext` so we
  can rotate the algorithm later without touching call sites.
- Activity logging is wrapped in a sub-transaction (savepoint via
  `db.begin_nested()`) so a failed log never poisons the parent
  transaction. The previous implementation called `db.commit()` inside
  the helper, which silently committed *unrelated* in-flight changes.
- `verify_password` swallows passlib's internal errors and returns False,
  preventing any chance of an exception leaking auth-related details to
  the client.
"""

from typing import Optional

from passlib.context import CryptContext
from sqlmodel import Session

import models


# `bcrypt` is deliberately the only scheme. `deprecated="auto"` means if
# we add a new scheme later, old hashes will be transparently re-hashed
# on the next successful login.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # OWASP-recommended minimum cost factor
)


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Constant-time password verification.
    Returns False on any internal error (e.g. corrupted hash) instead of
    raising, so the login route can treat all failures uniformly.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def log_activity(
    db: Session,
    user_id: Optional[int],
    details: str,
) -> None:
    """
    Append an audit-log entry. Uses a SAVEPOINT so the caller's
    transaction is unaffected if the log insert fails for any reason.
    Never raises — logging must not break the user-facing operation.
    """
    if user_id is None:
        return
    try:
        with db.begin_nested():
            db.add(models.ActivityLog(user_id=user_id, details=details))
    except Exception as e:
        # Intentional: don't propagate. We *could* wire this into a real
        # logger (e.g. structlog) — for now stderr is fine.
        print(f"[activity-log] write failed: {e}")


# ---------------------------------------------------------------------------
# Backwards-compatibility aliases
# ---------------------------------------------------------------------------
# The old code called `utils.hash(...)` and `utils.verify(...)`. Renaming
# would break every router import. We keep aliases until the codebase is
# fully migrated. Prefer the new names in any new code.
hash = hash_password   # noqa: A001 (intentional shadow of builtin)
verify = verify_password
