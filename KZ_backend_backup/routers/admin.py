# routers/admin.py
import base64
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
import schemas, database, models, oauth2, utils

# تعريف الراوتر ببرفكس واحد فقط لضمان عمل الروابط بشكل صحيح
router = APIRouter(prefix="/admin", tags=["Admin"])

# ===========================================================================
# 1. إدارة المستخدمين (الأزرار اللي جانت عطلانة)
# ===========================================================================

@router.patch("/users/{user_id}/status")
def toggle_user_status(user_id: int, db: Session = Depends(database.get_db), current_admin: models.User = Depends(oauth2.check_admin_role)):
    user = db.get(models.User, user_id)
    if not user: raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    if user.id == current_admin.id: raise HTTPException(status_code=400, detail="لا يمكنك حظر نفسك")

    # عكس حالة النشاط
    user.is_active = not user.is_active
    action_ar = "تفعيل" if user.is_active else "تجميد"
    
    # سجل النشاط بالعربي
    utils.log_activity(db, current_admin.id, f"تم {action_ar} حساب المستخدم: {user.firstname} {user.lastname}")
    db.commit()
    return {"message": f"تم {action_ar} الحساب بنجاح"}

@router.delete("/users/{user_id}/delete")
def delete_user(user_id: int, db: Session = Depends(database.get_db), current_admin: models.User = Depends(oauth2.check_admin_role)):
    user = db.get(models.User, user_id)
    if not user: raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    if user.id == current_admin.id: raise HTTPException(status_code=400, detail="لا يمكنك حذف حسابك")

    user_name = f"{user.firstname} {user.lastname}"
    db.delete(user)
    
    # سجل النشاط بالعربي
    utils.log_activity(db, current_admin.id, f"تم حذف حساب المستخدم {user_name} نهائياً")
    db.commit()
    return {"message": "تم حذف المستخدم بنجاح"}
# ===========================================================================
# 1. إدارة التصنيفات (Categories)
# ===========================================================================

@router.get("/categories", response_model=List[schemas.CategoryResponse])
def get_categories_api(db: Session = Depends(database.get_db)):
    return db.exec(select(models.Category).order_by(models.Category.category_name)).all()
@router.post("/categories/", response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(database.get_db), _admin: models.User = Depends(oauth2.check_admin_role)):
    """إضافة تصنيف جديد"""
    db_cat = models.Category(category_name=category.category_name)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@router.put("/categories/{category_id}")
def update_category(category_id: int, category_update: schemas.CategoryCreate, db: Session = Depends(database.get_db), _admin: models.User = Depends(oauth2.check_admin_role)):
    """تعديل اسم تصنيف موجود"""
    db_cat = db.get(models.Category, category_id)
    if not db_cat: 
        raise HTTPException(status_code=404, detail="التصنيف غير موجود")
    db_cat.category_name = category_update.category_name
    db.commit()
    return {"message": "تم التحديث بنجاح"}

@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(database.get_db), _admin: models.User = Depends(oauth2.check_admin_role)):
    """حذف تصنيف"""
    db_cat = db.get(models.Category, category_id)
    if not db_cat: 
        raise HTTPException(status_code=404, detail="التصنيف غير موجود")
    db.delete(db_cat)
    db.commit()
    return {"message": "تم الحذف بنجاح"}


# ===========================================================================
# 2. إدارة طلبات المعلمين (Teacher Requests)
# ===========================================================================

# routers/admin.py
import base64

# routers/admin.py
@router.get("/teacher-requests", response_model=dict)
def get_teacher_requests(db: Session = Depends(database.get_db), status: str = "pending", offset: int = 0, limit: int = 5, _admin: models.User = Depends(oauth2.check_admin_role)):
    stmt = select(models.TeacherApproval, models.User).join(
        models.User, models.TeacherApproval.user_id == models.User.id
    ).where(models.TeacherApproval.status == status).order_by(models.TeacherApproval.id.desc())
    
    results = db.exec(stmt.offset(offset).limit(limit)).all()
    total = len(db.exec(select(models.TeacherApproval).where(models.TeacherApproval.status == status)).all())
    
    items = []
    for app, u in results:
        # هسة الكود راح يعبر الـ cv_link كـ نص عادي بدون تحويل معقد
        # حتى نضمن إن السيرفر ميوكع
        items.append({
            "id": u.id, 
            "firstname": u.firstname, 
            "lastname": u.lastname,
            "email": u.email,
            "phone": app.phone, 
            "cv_link": app.cv_link, 
            "bio": u.bio, 
            "birthday_date": str(u.birthday_date) if u.birthday_date else "غير محدد",
            "status": app.status
        })
    return {"items": items, "total": total}
@router.post("/users/{user_id}/promote-to-teacher")
def promote_to_teacher(
    user_id: int, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.check_admin_role)
):
    """الموافقة على طلب المعلم وتسجيل النشاط بالعربية"""
    approval = db.exec(select(models.TeacherApproval).where(
        models.TeacherApproval.user_id == user_id, 
        models.TeacherApproval.status == "pending"
    )).first()
    
    if not approval: 
        raise HTTPException(status_code=404, detail="لا يوجد طلب معلق")
    
    approval.status = "approved"
    user = db.get(models.User, user_id)
    teacher_role = db.exec(select(models.Role).where(models.Role.role_name == "teacher")).first()
    
    if teacher_role and teacher_role not in user.roles:
        user.roles.append(teacher_role)
    
    # تسجيل النشاط باللغة العربية
    utils.log_activity(db, current_user.id, f"تم قبول طلب {user.firstname} وترقيته لمعلم")
    db.commit()
    return {"message": "تمت ترقية المستخدم بنجاح"}

@router.post("/users/{user_id}/reject-teacher-request")
def reject_teacher_request(
    user_id: int, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.check_admin_role)
):
    """رفض الطلب وتسجيل النشاط بالعربية"""
    approval = db.exec(select(models.TeacherApproval).where(
        models.TeacherApproval.user_id == user_id, 
        models.TeacherApproval.status == "pending"
    )).first()
    
    if not approval: 
        raise HTTPException(status_code=404, detail="لا يوجد طلب معلق")
    
    approval.status = "rejected"
    user = db.get(models.User, user_id)
    
    # تسجيل النشاط باللغة العربية
    utils.log_activity(db, current_user.id, f"تم رفض طلب الترقية للمستخدم {user.firstname}")
    db.commit()
    return {"message": "تم رفض طلب الترقية"}

@router.post("/users/{user_id}/reset-teacher-request")
def reset_teacher_request(
    user_id: int, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.check_admin_role)
):
    """إعادة التفكير: إرجاع الطلب للمراجعة وسحب رتبة المعلم"""
    approval = db.exec(select(models.TeacherApproval).where(models.TeacherApproval.user_id == user_id)).first()
    user = db.get(models.User, user_id)
    
    if not approval:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    # سحب رتبة المعلم وإرجاع الحالة لـ pending
    user.roles = [r for r in user.roles if r.role_name != "teacher"]
    approval.status = "pending"
    
    # تسجيل النشاط باللغة العربية
    utils.log_activity(db, current_user.id, f"تم إعادة الطلب للمراجعة للمستخدم {user.firstname}")
    db.commit()
    return {"message": "تمت إعادة الطلب لقائمة الانتظار"}


# ===========================================================================
# 3. سجل النشاطات (Activity Logs)
# ===========================================================================

@router.get("/logs")
def get_admin_logs(db: Session = Depends(database.get_db), _admin: models.User = Depends(oauth2.check_admin_role)):
    """جلب سجل النشاطات مرتباً من الأحدث للأقدم"""
    return db.exec(select(models.ActivityLog).order_by(models.ActivityLog.timestamp.desc())).all()

@router.get("/stats")
def get_admin_stats(db: Session = Depends(database.get_db), _admin: models.User = Depends(oauth2.check_admin_role)):
    # حساب الأعداد من الداتابيس
    students_count = len(db.exec(select(models.UserRole).where(models.UserRole.role_id == 1)).all())
    teachers_count = len(db.exec(select(models.UserRole).where(models.UserRole.role_id == 2)).all())
    sessions_count = len(db.exec(select(models.SessionModel)).all())
    pending_requests = len(db.exec(select(models.TeacherApproval).where(models.TeacherApproval.status == "pending")).all())
    
    return {
        "students": students_count,
        "teachers": teachers_count,
        "sessions": sessions_count,
        "requests": pending_requests
    }