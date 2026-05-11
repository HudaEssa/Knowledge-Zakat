"""
Authentication endpoints (login, logout).

Security improvements:
- Identical 401 response for "user not found" and "wrong password",
  preventing user enumeration via timing or message differences.
- Both branches still call `verify_password`, which keeps total response
  time constant regardless of whether the email exists. (Otherwise an
  attacker could detect a missing email by the absence of the bcrypt
  delay.)
- Login now uses HTTP 401 (Unauthorized), which is the correct status
  for failed credentials. The previous code returned 403, which is
  semantically "you are authenticated but not allowed".
- Logout no longer pretends to do anything server-side beyond logging.
  We are using stateless JWTs, so true revocation requires a deny-list
  (out of scope for this PR). The frontend should drop its token.

BUG FIXES (May 2026):
1. The login route was raising 403 instead of 401 — the docstring said
   401 but the code used HTTP_403_FORBIDDEN. Fixed.
2. The "user not found" branch short-circuited *before* calling
   verify_password, leaking the existence of accounts via response
   time. Fixed by always running a bcrypt verify against a dummy hash
   when the user is missing, so the wall-clock cost is constant.
3. The logout function was missing its @router.post decorator entirely,
   so the endpoint did not exist on the server. The frontend was
   silently 404-ing on every logout. Fixed.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

import database
import models
import oauth2
import schemas
import utils
from crud import users as users_crud

from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Authentication"])


# A pre-computed bcrypt hash of a random string. We verify against this
# whenever the requested email does NOT exist, so the response time of
# a "user not found" path matches the response time of a "wrong password"
# path. Prevents user-enumeration via timing analysis.
_DUMMY_HASH = utils.hash_password("dummy-password-for-timing-defense-only")


@router.post("/login", response_model=schemas.Token)
@router.post("/token", response_model=schemas.Token)
@limiter.limit("5/minute")
def login(
    request: Request,  # required so SlowAPI can read the client IP
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
):
    """
    Exchange email + password for a JWT access token.

    Rate-limited to 5 attempts per minute per IP to slow down brute force.
    Returns 401 on bad credentials, 403 only when the account is disabled.
    """
    # OAuth2PasswordRequestForm calls the field `username` — we use it
    # as the email since that's our identifier.
    user = users_crud.get_user_by_email(db, user_credentials.username)

    # SECURITY FIX: always burn one bcrypt cycle so a missing user does
    # not respond faster than a wrong password. The boolean below is
    # evaluated either against the real hash or against the dummy hash,
    # which keeps total response time roughly constant.
    if user is None:
        utils.verify_password(user_credentials.password, _DUMMY_HASH)
        password_ok = False
    else:
        password_ok = utils.verify_password(
            user_credentials.password, user.hashed_password
        )

    if user is None or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="البريد الإلكتروني أو كلمة المرور غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        # 403 here is correct: the credentials are valid, but the account
        # has been disabled by an admin.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذا الحساب محظور",
        )

    # Build the access token. `sub` is the canonical identity claim that
    # oauth2.get_current_user looks up; the others are kept for backward
    # compatibility with frontend code that reads `user_id` / `id`.
    access_token = oauth2.create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "id": user.id,
        }
    )

    utils.log_activity(db, user.id, "User logged in")
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(database.get_db),
):
    """
    Stateless JWTs cannot truly be invalidated server-side without a
    deny-list. The Svelte frontend is expected to discard the token
    locally; we just record the event for the audit trail.

    BUG FIX: the @router.post decorator was missing in the previous
    version, so this function existed but was not actually registered
    as an endpoint. Calls from the frontend silently returned 404.
    """
    utils.log_activity(db, current_user.id, "User logged out")
    db.commit()
    return {"message": "Logged out"}