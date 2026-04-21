# routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import base64

import models, database, oauth2, utils

router = APIRouter(tags=["Admin"])

# ==========================================
# 1. إرجاع كل المستخدمين (لصفحة الإحصائيات)
# ==========================================
@router.get("/users/")
def read_all_users(db: Session = Depends(database.get_db)):
    return db.query(models.User).all()

# ==========================================
# 2. إرجاع سجل النشاطات (لصفحة رصد النشاطات)
# ==========================================
@router.get("/admin/logs")
def get_admin_activity_logs(db: Session = Depends(database.get_db), admin: models.User = Depends(oauth2.check_admin_role)):
    return db.query(models.ActivityLog).order_by(models.ActivityLog.timestamp.desc()).all()

# ==========================================
# 3. إرجاع طلبات المعلمين (مع كافة التفاصيل للنافذة المنبثقة)
# ==========================================
@router.get("/admin/teacher-requests")
def get_teacher_requests(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.check_admin_role)):
    results = db.query(models.TeacherApproval, models.User).join(
        models.User, models.TeacherApproval.user_id == models.User.id
    ).filter(models.TeacherApproval.status == "pending").all()
    
    response = []
    for approval, user in results:
        img_base64 = None
        if user.profile_image:
            img_base64 = f"data:image/jpeg;base64,{base64.b64encode(user.profile_image).decode()}"
            
        response.append({
            "id": user.id,
            "request_id": approval.id,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "email": user.email,
            "bio": user.bio or "لا توجد نبذة",
            "birthday_date": str(user.birthday_date) if user.birthday_date else "غير محدد",
            "cv_link": approval.cv_link,
            "phone": getattr(approval, 'phone', 'لم يقم بإدخال رقم'), # 👈 جلب الرقم
            "profile_image": img_base64
        })
    return response

# ==========================================
# 4. دالة الموافقة وترقية المستخدم إلى معلم
# ==========================================
@router.post("/admin/users/{user_id}/promote-to-teacher")
def promote_to_teacher(user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.check_admin_role)):
    # 1. ندور على الطلب المعلق الخاص بهذا المستخدم
    approval = db.query(models.TeacherApproval).filter(
        models.TeacherApproval.user_id == user_id, 
        models.TeacherApproval.status == "pending"
    ).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="لا يوجد طلب معلق لهذا المستخدم")
        
    # 2. نغير حالة الطلب إلى مقبول
    approval.status = "approved"
    
    # 3. نجيب المستخدم ونضيفله رول المعلم
    user = db.query(models.User).filter(models.User.id == user_id).first()
    teacher_role = db.query(models.Role).filter(models.Role.role_name == "teacher").first()
    
    if teacher_role and teacher_role not in user.roles:
        user.roles.append(teacher_role)
        
    # 4. نسجل الحركة باللوگ مال الأدمن
    utils.log_activity(db, current_user.id, f"تمت ترقية المستخدم {user.firstname} إلى معلم")
    
    db.commit()
    return {"message": "تمت ترقية المستخدم بنجاح"}

# ==========================================
# 5. حظر أو تفعيل حساب مستخدم
# ==========================================
@router.patch("/admin/users/{user_id}/status")
def toggle_user_status(user_id: int, db: Session = Depends(database.get_db), admin: models.User = Depends(oauth2.check_admin_role)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    
    # عكس الحالة الحالية
    user.is_active = not user.is_active
    db.commit()
    
    status_text = "تفعيل" if user.is_active else "حظر"
    utils.log_activity(db, admin.id, f"قام الأدمن بـ {status_text} المستخدم رقم {user_id}")
    return {"message": f"تم {status_text} المستخدم بنجاح", "is_active": user.is_active}

# ==========================================
# 6. تعديل حالة جلسة (قبول / إيقاف)
# ==========================================
@router.patch("/admin/sessions/{session_id}/status")
def toggle_session_status_admin(
    session_id: int, 
    new_status: str, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.check_admin_role)
):
    db_session = db.query(models.SessionModel).filter(models.SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")

    db_session.status = new_status
    db.commit()
    utils.log_activity(db, current_user.id, f"تعديل حالة الجلسة {session_id} إلى {new_status}")
    
    return {"message": "تم تحديث حالة الجلسة بنجاح", "status": new_status}

# ==========================================
# دالة رفض طلب المعلم
# ==========================================
@router.post("/admin/users/{user_id}/reject-teacher-request")
def reject_teacher_request(user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.check_admin_role)):
    # 1. ندور على الطلب المعلق الخاص بهذا المستخدم
    approval = db.query(models.TeacherApproval).filter(
        models.TeacherApproval.user_id == user_id, 
        models.TeacherApproval.status == "pending"
    ).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="لا يوجد طلب معلق لهذا المستخدم")
        
    # 2. نغير حالة الطلب إلى مرفوض (بدون ما نعطيه رول المعلم)
    approval.status = "rejected"
    
    # 3. نسجل الحركة باللوگ مال الأدمن
    user = db.query(models.User).filter(models.User.id == user_id).first()
    utils.log_activity(db, current_user.id, f"قام الأدمن برفض طلب المعلم للمستخدم {user.firstname}")
    
    db.commit()
    return {"message": "تم رفض الطلب بنجاح"}

# بداخل ملف routers/admin.py
@router.delete("/admin/users/{user_id}/delete")
def delete_user_permanently(user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.check_admin_role)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    # حذف المتعلقات أولاً لمنع Foreign Key Error
    db.query(models.ActivityLog).filter(models.ActivityLog.user_id == user_id).delete()
    db.query(models.Enrollment).filter(models.Enrollment.user_id == user_id).delete()
    
    db.delete(user)
    db.commit()
    return {"message": "تم حذف المستخدم بنجاح"}