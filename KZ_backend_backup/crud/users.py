"""
User-related database operations.

Routes call these functions instead of building queries inline. That
gives us:
- One canonical place to change a query (e.g. add filtering, eager
  loading) without grepping through every router.
- Easier unit testing — pass a real Session against an in-memory SQLite
  and you can exercise the CRUD layer without spinning up FastAPI.
- Routers stay short and focused on HTTP concerns (auth, status codes,
  serialization).
"""

from typing import List, Optional

from sqlmodel import Session, select
from sqlalchemy import func
import models
import schemas
import utils


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.exec(select(models.User).where(models.User.email == email)).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.get(models.User, user_id)


def get_all_users(db: Session, offset: int = 0, limit: int = 10):
    # حساب العدد الكلي قبل التقطيع
    total = db.exec(select(func.count(models.User.id))).one()
    
    # جلب المستخدمين حسب الصفحة المطلوبة
    query = select(models.User).offset(offset).limit(limit).order_by(models.User.firstname)
    items = list(db.exec(query).all())
    
    return {"items": items, "total": total}

# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_user(db: Session, payload: schemas.UserCreate) -> models.User:
    """
    Create a user with the default 'student' role attached.
    The caller is responsible for the duplicate-email check (the route
    returns a friendly 400; this layer would return a SQL integrity
    error otherwise).
    """
    new_user = models.User(
        firstname=payload.firstname,
        lastname=payload.lastname,
        email=payload.email,
        # NEVER store the plaintext password. utils.hash_password uses
        # bcrypt with a strong cost factor.
        hashed_password=utils.hash_password(payload.password),
        bio=payload.bio,
        birthday_date=payload.birthday_date,
    )

    student_role = db.exec(
        select(models.Role).where(models.Role.role_name == "student")
    ).first()
    if student_role:
        new_user.roles.append(student_role)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def update_user_profile(
    db: Session,
    db_user: models.User,
    payload: schemas.UserUpdate,
    *,
    allow_password_change: bool = True,
) -> models.User:
    """
    Apply a partial update.

    Password change rule: if `new_password` is supplied, `old_password`
    MUST also be supplied AND match the stored hash. The route layer is
    responsible for enforcing this (we want a 400/403, not a silent skip);
    this function just applies whatever the route has decided is valid.
    """
    if payload.firstname is not None:
        db_user.firstname = payload.firstname
    if payload.lastname is not None:
        db_user.lastname = payload.lastname
    if payload.bio is not None:
        db_user.bio = payload.bio
    if payload.birthday_date is not None:
        db_user.birthday_date = payload.birthday_date
    if payload.email is not None:
        db_user.email = payload.email

    if allow_password_change and payload.new_password:
        db_user.hashed_password = utils.hash_password(payload.new_password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def set_profile_image(
    db: Session, db_user: models.User, image_bytes: bytes
) -> models.User:
    db_user.profile_image = image_bytes
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def delete_user(db: Session, db_user: models.User) -> None:
    db.delete(db_user)
    db.commit()


# ---------------------------------------------------------------------------
# Enrollments owned by a user
# ---------------------------------------------------------------------------

def get_pending_enrollment(
    db: Session, user_id: int, session_id: int
) -> Optional[models.Enrollment]:
    return db.exec(
        select(models.Enrollment).where(
            models.Enrollment.user_id == user_id,
            models.Enrollment.session_id == session_id,
        )
    ).first()


def create_enrollment(
    db: Session, user_id: int, session_id: int
) -> models.Enrollment:
    new_enroll = models.Enrollment(
        user_id=user_id, session_id=session_id, status="pending"
    )
    db.add(new_enroll)
    db.commit()
    db.refresh(new_enroll)
    return new_enroll


def create_admin(db: Session, payload: schemas.AdminCreate) -> models.User:
    new_user = models.User(
        firstname=payload.firstname,
        lastname=payload.lastname,
        email=payload.email,
        phone=payload.phone,
        hashed_password=utils.hash_password(payload.password),
    )
    admin_role = db.exec(
        select(models.Role).where(models.Role.role_name == "admin")
    ).first()
    
    if admin_role:
        new_user.roles.append(admin_role)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user