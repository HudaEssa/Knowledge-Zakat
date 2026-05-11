"""
Session/category/enrollment database operations.

The router stays thin — see routers/sessions.py for HTTP-level concerns.
"""

from typing import List, Optional, Tuple

from sqlmodel import Session, select, or_

import models
import schemas


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

def get_category_by_name(db: Session, name: str) -> Optional[models.Category]:
    return db.exec(
        select(models.Category).where(models.Category.category_name == name)
    ).first()


def list_categories(db: Session) -> List[models.Category]:
    return list(db.exec(select(models.Category)).all())


def create_category(db: Session, name: str) -> models.Category:
    cat = models.Category(category_name=name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def update_category(
    db: Session, db_cat: models.Category, new_name: str
) -> models.Category:
    db_cat.category_name = new_name
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat


def delete_category(db: Session, db_cat: models.Category) -> None:
    db.delete(db_cat)
    db.commit()


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

# crud/sessions.py

def create_session(db: Session, owner_id: int, payload: schemas.SessionCreate):
    # 1. تحويل الـ Schema إلى قاموس (Dictionary)
    session_data = payload.model_dump()
    
    # 2. فصل الـ category_ids لأنها ليست حقلاً مباشراً في الجدول
    category_ids = session_data.pop("category_ids", [])
    
    # 3. إنشاء كائن المحاضرة (هنا الـ student_limit راح ينزل تلقائياً)
    new_session = models.SessionModel(
        **session_data,
        user_id=owner_id
    )
    
    # 4. ربط الأقسام العلمية بالمحاضرة (إذا كانت موجودة)
    if category_ids:
        categories = db.exec(
            select(models.Category).where(models.Category.id.in_(category_ids))
        ).all()
        new_session.categories = list(categories)
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

def list_sessions_with_teachers(
    db: Session, search: Optional[str] = None
) -> List[Tuple[models.SessionModel, models.User]]:
    """Return (session, teacher) tuples, optionally filtered by a free-text search."""
    stmt = select(models.SessionModel, models.User).join(
        models.User, models.SessionModel.user_id == models.User.id
    )
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                models.SessionModel.title.ilike(like),
                models.SessionModel.description.ilike(like),
            )
        )
    return list(db.exec(stmt).all())


def get_session(db: Session, session_id: int) -> Optional[models.SessionModel]:
    return db.get(models.SessionModel, session_id)


def update_session(
    db: Session,
    db_session: models.SessionModel,
    payload: schemas.SessionUpdate,
) -> models.SessionModel:
    update_data = payload.model_dump(exclude_unset=True)
    category_ids = update_data.pop("category_ids", None)

    for key, value in update_data.items():
        setattr(db_session, key, value)

    if category_ids is not None:
        db_session.categories = list(
            db.exec(
                select(models.Category).where(models.Category.id.in_(category_ids))
            ).all()
        )

    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def delete_session(db: Session, db_session: models.SessionModel) -> None:
    db.delete(db_session)
    db.commit()


def count_enrollments_for_session(db: Session, session_id: int) -> int:
    """Total enrollment rows on a session — regardless of status."""
    return len(
        list(
            db.exec(
                select(models.Enrollment).where(
                    models.Enrollment.session_id == session_id
                )
            ).all()
        )
    )


# ---------------------------------------------------------------------------
# Enrollments
# ---------------------------------------------------------------------------

def get_enrollment(
    db: Session, user_id: int, session_id: int
) -> Optional[models.Enrollment]:
    return db.exec(
        select(models.Enrollment).where(
            models.Enrollment.user_id == user_id,
            models.Enrollment.session_id == session_id,
        )
    ).first()


def update_enrollment_status(
    db: Session, enrollment: models.Enrollment, new_status: str
) -> models.Enrollment:
    enrollment.status = new_status
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment
