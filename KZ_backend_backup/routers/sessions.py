"""
Session/category/enrollment database operations.
Refactored for Knowledge Zakat - Teacher Update Support + Capacity.
"""
import base64
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from fastapi.responses import Response
from sqlmodel import Session, select, or_, func, update

from crud import sessions as crud_sessions # تأكدي من استيراد ملف الـ crud
import database 
import models
import schemas
import oauth2
import utils

# مسارات الرفع
PROFILE_UPLOAD_DIR = Path("static/profile_images")
PROFILE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"]
)


@router.get("/categories", response_model=List[schemas.CategoryResponse])
def get_categories_api(db: Session = Depends(database.get_db)):
    return list_categories(db)
# ---------------------------------------------------------------------------
# Categories Functions
# ---------------------------------------------------------------------------

def get_category_by_name(db: Session, name: str) -> Optional[models.Category]:
    return db.exec(select(models.Category).where(models.Category.category_name == name)).first()

def list_categories(db: Session) -> List[models.Category]:
    return list(db.exec(select(models.Category)).all())

def create_category(db: Session, name: str) -> models.Category:
    cat = models.Category(category_name=name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

def update_category(db: Session, db_cat: models.Category, new_name: str) -> models.Category:
    db_cat.category_name = new_name
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

def delete_category(db: Session, db_cat: models.Category) -> None:
    db.delete(db_cat)
    db.commit()

# ---------------------------------------------------------------------------
# Capacity helpers (NEW)
# ---------------------------------------------------------------------------
# Used by the enrollment endpoint to enforce `student_limit`. Kept in
# this module so the router stays a thin dispatch layer.

def count_accepted_enrollments(db: Session, session_id: int) -> int:
    """
    Number of enrollments with status='approved' on a session.
    Pending/rejected applicants do NOT take up a seat.
    """
    return db.exec(
        select(func.count(models.Enrollment.user_id)).where(
            models.Enrollment.session_id == session_id,
            models.Enrollment.status == "approved",
        )
    ).one()


def session_has_capacity(
    db: Session, session_obj: models.SessionModel
) -> bool:
    """
    Returns True if a session has room for one more approved student.
    Sessions with `student_limit=None` are unlimited and always return True.
    """
    if session_obj.student_limit is None:
        return True
    return count_accepted_enrollments(db, session_obj.id) < session_obj.student_limit


# ---------------------------------------------------------------------------
# Sessions Functions
# ---------------------------------------------------------------------------

# 1. تأكدي إنّو هذا السطر موجود فوگ الدالة مباشرةً
# routers/sessions.py

@router.post("/", response_model=schemas.SessionResponse) 
def create_session(
    payload: schemas.SessionCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # استدعاء دالة الـ CRUD وتمرير البيانات لها
    return crud_sessions.create_session(
        db=db, 
        owner_id=current_user.id, 
        payload=payload
    )
def list_sessions_with_teachers(db: Session, search: Optional[str] = None) -> List[Tuple[models.SessionModel, models.User]]:
    stmt = select(models.SessionModel, models.User).join(models.User, models.SessionModel.user_id == models.User.id)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(models.SessionModel.title.ilike(like), models.SessionModel.description.ilike(like)))
    return list(db.exec(stmt).all())

def get_session_internal(db: Session, session_id: int) -> Optional[models.SessionModel]:
    return db.get(models.SessionModel, session_id)

def update_session_internal(db: Session, db_session: models.SessionModel, payload: schemas.SessionUpdate) -> models.SessionModel:
    update_data = payload.model_dump(exclude_unset=True)
    category_ids = update_data.pop("category_ids", None)
    for key, value in update_data.items():
        setattr(db_session, key, value)
    if category_ids is not None:
        db_session.categories = list(db.exec(select(models.Category).where(models.Category.id.in_(category_ids))).all())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def delete_session_internal(db: Session, db_session: models.SessionModel) -> None:
    db.delete(db_session)
    db.commit()

# ---------------------------------------------------------------------------
# HTTP Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[schemas.SessionResponse])
def get_all_sessions(db: Session = Depends(database.get_db)):
    rows = list_sessions_with_teachers(db)
    results = []
    for s, u in rows:
        session_dict = s.model_dump()
        session_dict["teacher_id"] = u.id  
        
        # 👈 التعديل الثاني: إرسال الأقسام (Categories) حتى تشتغل الفلترة
        session_dict["categories"] = [c.model_dump() for c in s.categories] if s.categories else []
        session_dict["teacher_name"] = f"{u.firstname} {u.lastname}"
        # 👈 إضافة عدد المقبولين فعلياً حتى يعرضه الـ frontend
        # كـ "X / Y مقعد" أو "ممتلئ" بدون استعلام إضافي.
        session_dict["accepted_count"] = count_accepted_enrollments(db, s.id)
        results.append(session_dict)
    return results


@router.get("/{session_id}")
def get_single_session(session_id: int, db: Session = Depends(database.get_db)):
    """جلب بيانات المحاضرة للتعديل - مينما"""
    session = db.get(models.SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="المحاضرة غير موجودة")
    result = session.model_dump()
    # ربط القسم لسهولة العرض في select
    result["category_id"] = session.categories[0].id if session.categories else None
    # عدد المقبولين — حتى الـ teacher يشوف هل يكدر يكبر السعة أو لا.
    result["accepted_count"] = count_accepted_enrollments(db, session.id)
    return result


@router.get("/{session_id}/details")
def get_session_details(session_id: int, db: Session = Depends(database.get_db)):
    """جلب تفاصيل المحاضرة مع عداد المقبولين والسعة - نسخة مينما المعدلة"""
    stmt = select(models.SessionModel, models.User).join(models.User).where(models.SessionModel.id == session_id)
    result = db.exec(stmt).first()
    if not result:
        raise HTTPException(status_code=404, detail="المحاضرة غير موجودة")
    
    session_obj, teacher = result

    # 👈 إضافة: حساب عدد المقبولين فعلياً
    accepted_count = count_accepted_enrollments(db, session_id)

    # (باقي حسابات التقييمات مالتج...)
    ratings_stmt = select(models.Rating).where(models.Rating.session_id == session_id)
    ratings = db.exec(ratings_stmt).all()
    avg_session = sum(r.session_rate for r in ratings) / len(ratings) if ratings else 0
    teacher_ratings = db.exec(select(models.Rating).where(models.Rating.teacher_id == teacher.id)).all()
    avg_teacher = sum(r.teacher_rate for r in teacher_ratings) / len(teacher_ratings) if teacher_ratings else 0

    # (جزء التعليقات مالتج يبقى نفسه...)
    # ---------------------------------------------------------
    # 1. جلب كل التعليقات (الأساسية والردود) بضربة وحدة للداتا بيس
    # ---------------------------------------------------------
    # 1. جلب كل التعليقات (الأساسية والردود) بضربة وحدة للداتا بيس
    comments_query = (
        select(models.Comment, models.User)
        .join(models.User, isouter=True)
        .where(models.Comment.session_id == session_id)
    )
    all_comments_data = db.exec(comments_query).all()

    # 2. بناء شجرة التعليقات بالذاكرة (Python Memory) لتسريع الأداء
    comments_dict = {}
    formatted_comments = []

    # تهيئة كل التعليقات وتحويلها لـ Dictionary
    for comment, user in all_comments_data:
        comments_dict[comment.id] = {
            "id": comment.id,
            "content": comment.content,
            "user_id": comment.user_id,
            "created_at": comment.created_at.isoformat() if comment.created_at else "",
            "user_name": f"{user.firstname} {user.lastname}" if user else "مستخدم",
            "user_image": f"data:image/jpeg;base64,{base64.b64encode(user.profile_image).decode()}" if user and user.profile_image else None,
            "parent_id": comment.parent_id,
            "replies": []
        }

    # ربط الردود بآبائها
    for c_id, c_data in comments_dict.items():
        if c_data["parent_id"] is None:
            # تعليق أساسي
            formatted_comments.append(c_data)
        else:
            # رد على تعليق
            parent_id = c_data["parent_id"]
            if parent_id in comments_dict:
                comments_dict[parent_id]["replies"].append(c_data)

    return {
        "session": {
            "id": session_obj.id,
            "title": session_obj.title,
            "description": session_obj.description,
            "cover": session_obj.cover_image_url,
            "meeting_link": session_obj.meeting_link,
            "student_limit": getattr(session_obj, 'student_limit', None)
        },
        "accepted_count": accepted_count,
        "teacher_id": teacher.id,
        "teacher_name": f"{teacher.firstname} {teacher.lastname}",
        "avg_session_rating": avg_session,
        "avg_teacher_rating": avg_teacher,
        "ratings_count": len(ratings),
        "comments": formatted_comments
    }

@router.put("/{session_id}")
def update_session_endpoint(session_id: int, payload: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    db_session = db.get(models.SessionModel, session_id)
    if not db_session or db_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # 👈 منع المعلم من تخفيض السعة لأقل من عدد المقبولين حالياً.
    # مثال: عنده 5 مقبولين ويحاول يخفض السعة لـ 3 — نرفض.
    if "student_limit" in payload and payload["student_limit"] is not None:
        accepted_now = count_accepted_enrollments(db, session_id)
        if payload["student_limit"] < accepted_now:
            raise HTTPException(
                status_code=400,
                detail=f"لا يمكن تخفيض السعة لأقل من عدد المقبولين الحالي ({accepted_now})"
            )

    for key, value in payload.items():
        if key != "category_ids" and hasattr(db_session, key):
            setattr(db_session, key, value)
            
    if "category_ids" in payload:
        cats = db.exec(select(models.Category).where(models.Category.id.in_(payload["category_ids"]))).all()
        db_session.categories = list(cats)
        
    db.add(db_session)
    db.commit()
    return {"message": "Success"}

@router.delete("/{session_id}")
def delete_session_api(session_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    db_s = db.get(models.SessionModel, session_id)
    if not db_s or db_s.user_id != current_user.id: raise HTTPException(status_code=403)
    db.delete(db_s)
    db.commit()
    return {"message": "Deleted"}

@router.post("/upload-cv")
async def upload_cv_api(file: UploadFile = File(...), current_user: models.User = Depends(oauth2.get_current_user)):
    raw = await file.read()
    unique_filename = f"cv_{uuid.uuid4().hex}.pdf"
    path = PROFILE_UPLOAD_DIR / unique_filename
    with open(path, "wb") as f: f.write(raw)
    return {"cv_link": f"/static/profile_images/{unique_filename}"}

@router.patch("/enrollments/update")
def update_enroll_status(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # 👈 فحص السعة قبل القبول.
    # لو المعلم يحاول يقبل طالب على محاضرة وصلت سعتها، نرفض.
    if data.get("status") == "approved":
        session_obj = db.get(models.SessionModel, data["session_id"])
        if session_obj and session_obj.student_limit is not None:
            accepted_now = count_accepted_enrollments(db, session_obj.id)
            if accepted_now >= session_obj.student_limit:
                raise HTTPException(
                    status_code=400,
                    detail="اكتمل العدد المسموح به، لا يمكن قبول طلاب إضافيين"
                )

    stmt = update(models.Enrollment).where(models.Enrollment.user_id == data["user_id"], models.Enrollment.session_id == data["session_id"]).values(status=data["status"])
    db.exec(stmt)
    db.commit()
    return {"message": "Updated"}

# ---------------------------------------------------------------------------
# Comments Logic (إضافة التعليقات والردود)
# ---------------------------------------------------------------------------

@router.post("/comments/")
def create_comment(
    payload: dict, # يستقبل session_id, content, و parent_id
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """إضافة تعليق جديد أو رد على تعليق"""
    session_id = payload.get("session_id")
    content = payload.get("content")
    parent_id = payload.get("parent_id") # يكون None إذا كان تعليق أساسي

    if not content or not session_id:
        raise HTTPException(status_code=400, detail="بيانات التعليق ناقصة")

    # إنشاء كائن التعليق
    new_comment = models.Comment(
        content=content,
        session_id=session_id,
        user_id=current_user.id,
        parent_id=parent_id,
        created_at=datetime.now()
    )
    
    db.add(new_comment)
    utils.log_activity(db, current_user.id, f"أضاف تعليقاً على المحاضرة رقم {session_id}")
    db.commit()
    db.refresh(new_comment)
    
    return {"status": "success", "comment_id": new_comment.id}

# ---------------------------------------------------------------------------
# تحديث وحذف التعليقات
# ---------------------------------------------------------------------------

@router.put("/comments/{comment_id}")
def update_comment(
    comment_id: int,
    payload: dict,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """تعديل محتوى التعليق"""
    db_comment = db.get(models.Comment, comment_id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="التعليق غير موجود")
    if db_comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="لا يمكنك تعديل تعليق شخص آخر")

    db_comment.content = payload.get("content", db_comment.content)
    db.add(db_comment)
    db.commit()
    return {"status": "updated"}

@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """حذف التعليق نهائياً"""
    db_comment = db.get(models.Comment, comment_id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="التعليق غير موجود")
    if db_comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="لا يمكنك حذف تعليق شخص آخر")

    db.delete(db_comment)
    db.commit()
    return {"status": "deleted"}


# داخل ملف routers/sessions.py




@router.post("/ratings/")
def submit_rating(
    payload: dict,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    session_id = payload.get("session_id")
    teacher_id = payload.get("teacher_id")
    session_rate = payload.get("session_rate")
    teacher_rate = payload.get("teacher_rate")

    if not session_id or not teacher_id:
        raise HTTPException(status_code=400, detail="بيانات التقييم ناقصة")

    # 1. التحقق من الانضمام (يجب أن يكون الطالب مشترك ومقبول)
    enrollment = db.exec(
        select(models.Enrollment).where(
            models.Enrollment.user_id == current_user.id,
            models.Enrollment.session_id == session_id,
            models.Enrollment.status == "approved"
        )
    ).first()

    if not enrollment:
        raise HTTPException(status_code=403, detail="لا يمكنك التقييم إلا بعد الانضمام للمحاضرة وموافقة المعلم.")

    # 2. التحقق من عدم التقييم المسبق
    existing = db.exec(
        select(models.Rating).where(
            models.Rating.user_id == current_user.id,
            models.Rating.session_id == session_id
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="لقد قمت بتقييم هذه المحاضرة مسبقاً")

    # 3. إضافة التقييم الجديد
    new_rating = models.Rating(
        user_id=current_user.id,
        session_id=session_id,
        teacher_id=teacher_id,
        session_rate=session_rate,
        teacher_rate=teacher_rate
    )
    db.add(new_rating)
    db.commit()
    
    return {"message": "تم التقييم "}



@router.get("/notifications/all")
def get_all_notifications(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    notifications = []

    # --- 1. قسم المعلم (طلبات انضمام جديدة) ---
    teacher_stmt = (
        select(models.Enrollment, models.User.firstname, models.SessionModel.title)
        .join(models.User, models.Enrollment.user_id == models.User.id)
        .join(models.SessionModel, models.Enrollment.session_id == models.SessionModel.id)
        .where(models.SessionModel.user_id == current_user.id) # أنتِ صاحبة المحاضرة
        .where(models.Enrollment.status == "pending")
        .where(models.Enrollment.notification_seen == False) # طلبات بانتظار الموافقة
    )
    teacher_results = db.exec(teacher_stmt).all()
    
    for en, student_fname, session_title in teacher_results:
        notifications.append({
            "id": f"req_{en.user_id}_{en.session_id}",
            "type": "new_request",
            "title": "طلب انضمام جديد 👤",
            "message": f"الطالب {student_fname} ينتظر موافقتك على '{session_title}'.",
            "target_page": "teacher_requests"
        })

    # --- 2. قسم الطالب (تحديثات على طلباتك أنتِ) ---
    student_stmt = (
        select(models.Enrollment, models.SessionModel.title, models.SessionModel.id)
        .join(models.SessionModel, models.Enrollment.session_id == models.SessionModel.id)
        .where(models.Enrollment.user_id == current_user.id) # أنتِ الطالبة اللي قدمتي
        .where(models.Enrollment.status.in_(["approved", "rejected"]))
        .where(models.Enrollment.notification_seen == False)
    )
    
    student_results = db.exec(student_stmt).all()
    
    for en, session_title, session_id in student_results:
        # تحديد الحالة
        is_approved = en.status == "approved"
        
        notifications.append({
            "id": f"st_{en.session_id}_{en.status}",
            "type": en.status, # approved أو rejected
            "title": "تمت الموافقة " if is_approved else " تم الرفض",
            "message": f"تم قبولك في محاضرة '{session_title}' " if is_approved else f"نعتذر، تم رفض طلبك في '{session_title}'.",
            "target_page": "my_learning" if is_approved else None, # الرفض ميروح لمكان
            "session_id": session_id 
        })

    return notifications

# مسح تنبيه واحد
@router.delete("/notifications/{session_id}")
def delete_notification(
    session_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # نحدث حالة التسجيل لتكون "مقروءة" فلا تظهر بالجرس
    enrollment = db.exec(
        select(models.Enrollment)
        .where(models.Enrollment.session_id == session_id, models.Enrollment.user_id == current_user.id)
    ).first()
    
    if enrollment:
        enrollment.notification_seen = True # تأكدي من إضافة هذا الحقل للمودل
        db.add(enrollment)
        db.commit()
    return {"status": "deleted"}

# مسح الكل
@router.delete("/notifications/clear-all")
def clear_all_notifications(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # نحدث كل التسجيلات الخاصة بالمستخدم لتكون "شوهدت"
    enrollments = db.exec(
        select(models.Enrollment).where(models.Enrollment.user_id == current_user.id)
    ).all()
    
    for en in enrollments:
        en.notification_seen = True
        db.add(en)
        
    db.commit()
    return {"status": "all cleared"}