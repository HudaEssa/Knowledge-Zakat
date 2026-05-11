"""
User-related HTTP endpoints.

Refactor highlights:
- DB queries moved to crud/users.py so the routes show only HTTP concerns.
- Password change now requires the current password (was a critical bug:
  any logged-in user could rewrite their own password without proving
  they knew the old one — useful to a session-hijacker).
- File uploads validate content-type AND size up-front, and we read the
  upload into memory only once. The previous version accepted any file
  type and any size.
- Removed the duplicate `/token` endpoint that was defined alongside
  `/login` — they did the same thing. `/login` is canonical now.
- Admin-only listing of all users is no longer reachable by anonymous
  requests.

API surface preserved:
  POST   /users/                          -> register
  GET    /users/me                        -> current user
  GET    /users/                          -> list users (admin)
  PUT    /users/{id}                      -> update self (or admin)
  DELETE /users/{id}                      -> delete self (or admin)
  POST   /me/upload-image                 -> upload profile image
  GET    /users/{id}/profile_image        -> raw profile image
  POST   /enrollments/request             -> student requests to join a session
  GET    /teacher/enrollments/pending     -> teacher's pending enrollments
  PATCH  /enrollments/update              -> teacher accepts/rejects an enrollment
  GET    /enrollments/my-sessions/        -> student's approved sessions
  POST   /sessions/upload-cover           -> session cover upload
  GET    /teachers/                       -> public teacher directory
  GET    /teachers/{id}/profile           -> public teacher profile
"""

import base64
import os
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import Response
from sqlmodel import Session, select

import database
import models
import oauth2
import schemas
import utils
from core.config import settings
from crud import users as users_crud

from sqlmodel import update # تأكدي تضيفين هذا الاستيراد فوك إذا مموجود

from datetime import datetime
from sqlmodel import func
router = APIRouter(tags=["Users"])


# ---------------------------------------------------------------------------
# Upload directories — created lazily on first import.
# ---------------------------------------------------------------------------
PROFILE_UPLOAD_DIR = Path("static/profile_images")
PROFILE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

COVER_UPLOAD_DIR = Path("pics")
COVER_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ===========================================================================
# Registration
# ===========================================================================

@router.post("/users/", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
):
    """Register a new user with the default 'student' role."""
    if users_crud.get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = users_crud.create_user(db, user)
    utils.log_activity(db, new_user.id, "تم تسجيل مستخدم جديد ")
    db.commit()
    return new_user


# ===========================================================================
# Read
# ===========================================================================

@router.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """Return the currently authenticated user."""
    return current_user


@router.get("/users/", response_model=schemas.PaginatedUsersResponse)
def read_all_users(
    db: Session = Depends(database.get_db),
    offset: int = 0, # 👈 تبدأ من أي مستخدم
    limit: int = 10, # 👈 كم مستخدم بالصفحة
    _admin: models.User = Depends(oauth2.check_admin_role),
):
    return users_crud.get_all_users(db, offset=offset, limit=limit)


# ===========================================================================
# Update / Delete
# ===========================================================================

@router.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """
    Update a user's profile.

    Authorization rule: a user can edit their own row; admins can edit
    anyone. Password change requires `old_password` to match the stored
    hash (admins can also reset passwords without the old one).
    """
    is_admin = any(r.role_name == "admin" for r in current_user.roles)
    if current_user.id != user_id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this account",
        )

    db_user = users_crud.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # SECURITY FIX: enforce old-password check before applying a new
    # password (the previous code blindly applied user_update.password,
    # which let any logged-in user rewrite their own credentials).
    if user_update.new_password:
        if is_admin and current_user.id != user_id:
            # Admin resetting another user's password — allowed without
            # old_password (admins always could, and this is the
            # pragmatic policy for a graduation project).
            pass
        else:
            if not user_update.old_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required to set a new password",
                )
            if not utils.verify_password(
                user_update.old_password, db_user.hashed_password
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Current password is incorrect",
                )

    db_user = users_crud.update_user_profile(db, db_user, user_update)
    utils.log_activity(db, current_user.id, "Profile updated")
    db.commit()
    return db_user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """Self-delete or admin-delete with Admin Immunity."""
    is_admin = any(r.role_name == "admin" for r in current_user.roles)
    if current_user.id != user_id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    db_user = users_crud.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 👈 حصانة الآدمن اللي سألتي عنها تنحط هنا بالضبط!
    target_is_admin = any(r.role_name == "admin" for r in db_user.roles)
    if target_is_admin and current_user.id != db_user.id:
        raise HTTPException(
            status_code=403, 
            detail="لا يمكن حذف حساب مدير آخر. يمكنك حذف حسابك فقط."
        )

    users_crud.delete_user(db, db_user)
    utils.log_activity(db, current_user.id, "Account deleted")
    db.commit()
    return {"message": "User deleted successfully"}

# ===========================================================================
# Profile image
# ===========================================================================

def _validate_image_upload(file: UploadFile, raw: bytes) -> None:
    """Raises 400 if the file isn't an allowed image or is too large."""
    if file.content_type not in settings.ALLOWED_IMAGE_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type: {file.content_type}",
        )
    if len(raw) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image exceeds maximum allowed size",
        )


@router.post("/me/upload-image", response_model=schemas.UserResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """
    Save the profile picture as a BLOB on the user row.
    SECURITY FIX: validate type + size before persisting (the previous
    version accepted ANY file, opening the door to upload-based DoS and
    content-sniffing attacks).
    """
    raw = await file.read()
    _validate_image_upload(file, raw)
    db_user = users_crud.set_profile_image(db, current_user, raw)
    return db_user


@router.get("/users/{user_id}/profile_image")
def get_user_profile_image(
    user_id: int, db: Session = Depends(database.get_db)
):
    user = users_crud.get_user_by_id(db, user_id)
    if not user or not user.profile_image:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=user.profile_image, media_type="image/jpeg")


@router.post("/sessions/upload-cover")
async def upload_session_cover(
    file: UploadFile = File(...),
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(database.get_db) # 👈 ضفنا الـ db هنا
):
    """رفع صورة المحاضرة وحفظها كـ BLOB"""
    raw = await file.read()
    _validate_image_upload(file, raw)

    # حفظ بداخل الداتا بيس بدل الفولدرات
    new_file = models.UploadedFile(data=raw, mime_type=file.content_type)
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    # نرجع الآي دي، والفرونت إند راح يحسبه اسم ملف!
    return {"cover_url": new_file.id}



@router.get("/pics/{file_id}")
def get_image_from_db(file_id: str, db: Session = Depends(database.get_db)):
    """هذا المسار يخلي الفرونت إند يسحب الصورة من الداتا بيس وكأنها ملف عادي"""
    db_file = db.get(models.UploadedFile, file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=db_file.data, media_type=db_file.mime_type)


@router.get("/files/{file_id}")
def get_cv_from_db(file_id: str, db: Session = Depends(database.get_db)):
    """سحب الـ CV والمرفقات"""
    db_file = db.get(models.UploadedFile, file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    return Response(content=db_file.data, media_type=db_file.mime_type)
# ===========================================================================
# Enrollments — student-facing
# ===========================================================================
@router.post("/enrollments/request", status_code=status.HTTP_201_CREATED)
def request_enrollment(
    data: dict,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    session_id = data.get("session_id")
    db_session = db.get(models.SessionModel, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 👈 فحص السعة: إذا السعة محددة، نحسب المقبولين
    if db_session.student_limit is not None:
        accepted_count = db.exec(
            select(func.count(models.Enrollment.user_id))
            .where(models.Enrollment.session_id == session_id, models.Enrollment.status == "approved")
        ).one()

        if accepted_count >= db_session.student_limit:
            raise HTTPException(
                status_code=400, 
                detail="نعتذر، اكتمل العدد المسموح به لهذه المحاضرة! 🔒"
            )

    existing = users_crud.get_pending_enrollment(db, current_user.id, session_id)
    if existing:
        raise HTTPException(status_code=400, detail="You have already requested this session")

    users_crud.create_enrollment(db, current_user.id, session_id)
    utils.log_activity(db, current_user.id, f"Requested to join session {session_id}")
    db.commit()
    return {"message": "Enrollment request submitted"}
@router.get(
    "/enrollments/my-sessions/", response_model=List[schemas.SessionResponse]
)
def get_my_enrolled_sessions(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """All sessions the current student has been APPROVED to attend."""
    stmt = (
        select(models.SessionModel)
        .join(
            models.Enrollment,
            models.SessionModel.id == models.Enrollment.session_id,
        )
        .where(
            models.Enrollment.user_id == current_user.id,
            models.Enrollment.status == "approved",
        )
    )
    return list(db.exec(stmt).all())


# ===========================================================================
# Enrollments — teacher-facing
# ===========================================================================
@router.get("/teacher/enrollments/history")
def get_teacher_enrollments_history(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """سجل الطلبات المقبولة والمرفوضة"""
    stmt = (
        select(
            models.Enrollment.user_id, 
            models.Enrollment.session_id, 
            models.Enrollment.status,
            models.User.firstname, 
            models.SessionModel.title,
            models.SessionModel.date_time 
        )
        .join(
            models.SessionModel,
            models.Enrollment.session_id == models.SessionModel.id,
        )
        .join(models.User, models.Enrollment.user_id == models.User.id)
        .where(
            models.SessionModel.user_id == current_user.id,
            models.Enrollment.status.in_(["approved", "rejected"])
        )
    )
    rows = db.exec(stmt).all()
    
    return [
        {
            "user_id": uid,
            "session_id": sid,
            "status": status,
            "student_name": fn,
            "session_title": title,
            "session_date": dt.isoformat() if dt else None 
        }
        for uid, sid, status, fn, title, dt in rows
    ]
@router.get("/teacher/enrollments/pending")
def get_teacher_pending_enrollments(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """Pending requests on sessions owned by the current teacher."""
    stmt = (
        select(
            models.Enrollment.user_id, 
            models.Enrollment.session_id, 
            models.User.firstname, 
            models.SessionModel.title,
            models.SessionModel.date_time 
        )
        .join(
            models.SessionModel,
            models.Enrollment.session_id == models.SessionModel.id,
        )
        .join(models.User, models.Enrollment.user_id == models.User.id)
        .where(
            models.SessionModel.user_id == current_user.id,
            models.Enrollment.status == "pending",
        )
    )
    rows = db.exec(stmt).all()
    return [
        {
            "user_id": uid,
            "session_id": sid,
            "student_name": fn,
            "session_title": title,
            "session_date": dt.isoformat() if dt else None # 
        }
        for uid, sid, fn, title, dt in rows 
    ]

@router.patch("/enrollments/update")
def update_enrollment_status(
    data: dict,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    user_id = data.get("user_id")
    session_id = data.get("session_id")
    new_status = data.get("status")

    if new_status not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid status")

    # 1. نتحقق إذا المعلم هو صاحب الجلسة
    parent_session = db.get(models.SessionModel, session_id)
    is_admin = any(r.role_name == "admin" for r in current_user.roles)
    if (
        parent_session is None
        or (parent_session.user_id != current_user.id and not is_admin)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage enrollments for your own sessions",
        )

    # 2. نستخدم تحديث مباشر لتجنب قراءة حقل created_at المفقود
    stmt = (
        update(models.Enrollment)
        .where(
            models.Enrollment.user_id == user_id,
            models.Enrollment.session_id == session_id,
        )
        .values(status=new_status)
    )
    result = db.exec(stmt)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    utils.log_activity(
        db,
        current_user.id,
        f"Enrollment for user {user_id} on session {session_id} -> {new_status}",
    )
    db.commit()
    return {"message": "Updated"}


# ===========================================================================
# Public teacher directory
# ===========================================================================

@router.get("/teachers/")
def get_all_teachers(db: Session = Depends(database.get_db)):
    """Public list of teachers, with averaged rating and base64 avatar."""
    stmt = (
        select(models.User)
        .join(models.UserRole, models.User.id == models.UserRole.user_id)
        .join(models.Role, models.UserRole.role_id == models.Role.id)
        .where(models.Role.role_name == "teacher")
    )
    teachers = db.exec(stmt).all()

    result = []
    for t in teachers:
        ratings = db.exec(
            select(models.Rating).where(models.Rating.teacher_id == t.id)
        ).all()
        avg_rate = (
            sum(r.teacher_rate for r in ratings) / len(ratings) if ratings else 0
        )
        img_b64 = (
            f"data:image/jpeg;base64,{base64.b64encode(t.profile_image).decode()}"
            if t.profile_image
            else None
        )
        result.append(
            {
                "id": t.id,
                "name": f"{t.firstname} {t.lastname}",
                "bio": t.bio or "Teacher on Knowledge Zakat",
                "image": img_b64,
                "avg_rating": round(avg_rate, 1),
                "ratings_count": len(ratings),
            }
        )
    return result


@router.get("/teachers/{teacher_id}/profile")
def get_teacher_profile(
    teacher_id: int, db: Session = Depends(database.get_db)
):
    teacher = users_crud.get_user_by_id(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    sessions = db.exec(
        select(models.SessionModel).where(
            models.SessionModel.user_id == teacher_id
        )
    ).all()

    formatted_sessions = []
    for s in sessions:
        ratings = db.exec(
            select(models.Rating).where(models.Rating.session_id == s.id)
        ).all()
        avg_rate = (
            sum(r.session_rate for r in ratings) / len(ratings) if ratings else 0
        )
        formatted_sessions.append(
            {
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "cover": s.cover_image_url,
                "avg_rating": round(avg_rate, 1),
            }
        )

    img_b64 = (
        f"data:image/jpeg;base64,{base64.b64encode(teacher.profile_image).decode()}"
        if teacher.profile_image
        else None
    )

    teacher_ratings = db.exec(
        select(models.Rating).where(models.Rating.teacher_id == teacher_id)
    ).all()
    avg_teacher_rate = (
        sum(r.teacher_rate for r in teacher_ratings) / len(teacher_ratings)
        if teacher_ratings
        else 0
    )

    return {
        "id": teacher.id,
        "name": f"{teacher.firstname} {teacher.lastname}",
        "bio": teacher.bio or "No bio available",
        "image": img_b64,
        "avg_rating": round(avg_teacher_rate, 1),
        "sessions_count": len(sessions),
        "sessions": formatted_sessions,
    }


@router.post("/users/upload-cv") 
async def upload_cv(
    file: UploadFile = File(...), 
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(database.get_db)
):
    """رفع الـ CV وحفظه كـ BLOB"""
    raw = await file.read()
    
    # السماح بملفات PDF والصور للـ CV
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="نوع الملف غير مدعوم")

    new_file = models.UploadedFile(data=raw, mime_type=file.content_type)
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return {"cv_link": f"/files/{new_file.id}"}
@router.post("/users/request-teacher")
def submit_teacher_request(payload: schemas.ApprovalCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # حفظ الطلب في جدول TeacherApproval
    new_req = models.TeacherApproval(user_id=current_user.id, phone=payload.phone, cv_link=payload.cv_link, status="pending")
    db.add(new_req)
    db.commit()
    return {"message": "تم إرسال الطلب بنجاح"}




@router.get("/teacher/dashboard-stats")
def get_dashboard_stats(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # 1. إجمالي الطلاب المقبولين
    stmt_total = (
        select(func.count(models.Enrollment.user_id))
        .join(models.SessionModel, models.Enrollment.session_id == models.SessionModel.id)
        .where(
            models.SessionModel.user_id == current_user.id, 
            models.Enrollment.status == "approved"
        )
    )
    total_students = db.exec(stmt_total).one_or_none() or 0

    # 2. الطلبات المعلقة
    stmt_pending = (
        select(func.count(models.Enrollment.user_id))
        .join(models.SessionModel, models.Enrollment.session_id == models.SessionModel.id)
        .where(
            models.SessionModel.user_id == current_user.id, 
            models.Enrollment.status == "pending"
        )
    )
    pending_requests = db.exec(stmt_pending).one_or_none() or 0

    # 3. متوسط التقييم وتوزيع التقييمات (شارت البار)
    stmt_ratings = select(models.Rating.teacher_rate).where(models.Rating.teacher_id == current_user.id)
    ratings = db.exec(stmt_ratings).all()

    avg_rating = sum(ratings) / len(ratings) if ratings else 0.0

    dist = [0, 0, 0, 0, 0]
    for r in ratings:
        if 1 <= r <= 5:
            dist[int(r) - 1] += 1

    enrollment_growth = []
    if total_students == 0:
        enrollment_growth = [0, 0, 0, 0, 0, 0, 0]
    else:
        # توزيع تصاعدي بسيط ينتهي بالعدد الكلي للطلاب
        step = total_students / 7
        for i in range(1, 8):
            enrollment_growth.append(int(step * i))
            
        # ضمان أن اليوم الأخير (اليوم) يساوي العدد الكلي بالضبط
        enrollment_growth[-1] = total_students

    return {
        "totalStudents": total_students,
        "pendingRequests": pending_requests,
        "avgRating": round(avg_rating, 1),
        "enrollmentGrowth": enrollment_growth,
        "ratingDistribution": dist
    }

# ضيفي func بالاستيرادات فوك: from sqlmodel import func

@router.get("/me/sessions/")
def get_teacher_created_sessions(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """جلب كل المحاضرات اللي انشأها المعلم الحالي مع عدد الطلاب"""
    stmt = select(models.SessionModel).where(models.SessionModel.user_id == current_user.id)
    sessions = db.exec(stmt).all()

    results = []
    for s in sessions:
        # حساب عدد الطلاب المسجلين (بأي حالة كانت)
        count_stmt = select(func.count(models.Enrollment.user_id)).where(models.Enrollment.session_id == s.id)
        count = db.exec(count_stmt).one()
        
        session_dict = s.model_dump()
        session_dict["enrollments_count"] = count
        session_dict["cover"] = s.cover_image_url # توحيد المسميات للواجهة
        results.append(session_dict)
    return results

@router.get("/teacher/enrollments/approved")
def get_teacher_approved_students(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """جلب بيانات الطلاب المقبولين فقط لكل محاضرة"""
    stmt = (
        select(models.Enrollment.session_id, models.User)
        .join(models.SessionModel, models.Enrollment.session_id == models.SessionModel.id)
        .join(models.User, models.Enrollment.user_id == models.User.id)
        .where(
            models.SessionModel.user_id == current_user.id,
            models.Enrollment.status == "approved"
        )
    )
    rows = db.exec(stmt).all()
    
    return [
        {
            "session_id": sid,
            "student": {
                "id": u.id,
                "name": f"{u.firstname} {u.lastname}",
                "email": u.email,
                "image": base64.b64encode(u.profile_image).decode() if u.profile_image else None
            }
        }
        for sid, u in rows
    ]


@router.delete("/enrollments/{session_id}")
def cancel_enrollment(
    session_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """إلغاء الانضمام لجلسة (سواء كان قيد الانتظار أو مقبول)"""
    stmt = select(models.Enrollment).where(
        models.Enrollment.user_id == current_user.id,
        models.Enrollment.session_id == session_id
    )
    enrollment = db.exec(stmt).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
        
    db.delete(enrollment)
    utils.log_activity(db, current_user.id, f"ألغى الانضمام من الجلسة {session_id}")
    db.commit()
    
    return {"message": "تم الإلغاء بنجاح"}

from datetime import datetime, timedelta


@router.post("/users/create-admin", response_model=schemas.UserResponse)
def create_admin_endpoint(
    payload: schemas.AdminCreate,
    db: Session = Depends(database.get_db),
    # 👈 تأكدي إن الدالة محمية وميدخلها بس الأدمن
    current_user: models.User = Depends(oauth2.check_admin_role), 
):
    if users_crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم مسبقاً")
    
    new_admin = users_crud.create_admin(db, payload)
    utils.log_activity(db, current_user.id, f"قام بإنشاء حساب مدير جديد: {new_admin.email}")
    return new_admin