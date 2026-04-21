import base64

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, database, utils, oauth2
from sqlalchemy import or_ 

router = APIRouter(tags=["Sessions & Categories"])

# --- Categories ---
@router.post("/categories/", response_model=schemas.CategoryResponse)
def create_category(cat: schemas.CategoryCreate, db: Session = Depends(database.get_db)):
    if db.query(models.Category).filter(models.Category.category_name == cat.category_name).first():
        raise HTTPException(status_code=400, detail="Category exists")
    new_cat = models.Category(category_name=cat.category_name)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@router.get("/categories/", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(database.get_db)):
    return db.query(models.Category).all()

# --- Sessions CRUD ---
@router.post("/sessions/", response_model=schemas.SessionResponse)
def create_session(session: schemas.SessionCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    category_ids_list = session.category_ids
    session_data = session.dict()
    session_data.pop("category_ids") 
    new_session = models.SessionModel(user_id=current_user.id, **session_data)
    if category_ids_list:
        categories = db.query(models.Category).filter(models.Category.id.in_(category_ids_list)).all()
        new_session.categories = categories
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    utils.log_activity(db, current_user.id, f"تم إنشاء جلسة جديدة: {new_session.title}") # 👈 تم التصحيح
    return new_session

@router.get("/sessions/", response_model=List[schemas.SessionResponse])
def get_sessions(search: Optional[str] = None, db: Session = Depends(database.get_db)):

    query = db.query(models.SessionModel, models.User).join(
        models.User, models.SessionModel.user_id == models.User.id
    )

    if search:
        query = query.filter(
            or_(
                models.SessionModel.title.ilike(f"%{search}%"),
                models.SessionModel.description.ilike(f"%{search}%")
            )
        )

    results = query.all()

    sessions_list = []

    for session, teacher in results:
        session_data = schemas.SessionResponse.model_validate(session)
        session_data.teacher_name = f"{teacher.firstname} {teacher.lastname}"
        
        # نرسل فقط الـ IDs والروابط، لا نرسل Base64 هنا
        session_data.teacher_id = teacher.id
        session_data.display_cover = session.cover_image_url # هذا هو اسم الملف في مجلد pics
        
        sessions_list.append(session_data)

    return sessions_list

# D:\Graduation_project\KZ_backend\routers\sessions.py

@router.put("/sessions/{session_id}", response_model=schemas.SessionResponse)
def update_session(session_id: int, session_update: schemas.SessionUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # 1. البحث عن الجلسة في قاعدة البيانات
    db_session = db.query(models.SessionModel).filter(models.SessionModel.id == session_id).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="المحاضرة غير موجودة")
        
    # 2. التأكد من أن المستخدم هو صاحب المحاضرة
    if db_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="غير مصرح لك بتعديل هذه المحاضرة")
    
    # 3. تحويل البيانات القادمة إلى قاموس وتحديث الحقول ديناميكياً
    # هذه الطريقة تضمن تحديث أي حقل مرسل (بما في ذلك الصورة والرابط)
    update_data = session_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        if key == "category_ids":
            if value is not None:
                db_session.categories = db.query(models.Category).filter(models.Category.id.in_(value)).all()
        else:
            # تحديث بقية الحقول مثل title, description, cover_image_url, meeting_link
            setattr(db_session, key, value)

    # 4. حفظ التغييرات في قاعدة البيانات
    db.commit()
    db.refresh(db_session)
    
    utils.log_activity(db, current_user.id, f"تحديث جلسة: تم تعديل الجلسة {session_id}")
    return db_session

@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    db_session = db.query(models.SessionModel).filter(models.SessionModel.id == session_id).first()
    if not db_session: raise HTTPException(status_code=404, detail="Session not found")
    is_admin = any(role.role_name == "admin" for role in current_user.roles)
    if not is_admin and db_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    log_msg = f"حذف الجلسة: {db_session.title}"
    db.delete(db_session)
    db.commit()
    utils.log_activity(db, current_user.id, log_msg)
    return {"message": "Session deleted successfully"}

@router.post("/sessions/{session_id}/enroll")
def enroll_in_session(session_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    session = db.query(models.SessionModel).filter(models.SessionModel.id == session_id).first()
    if not session: raise HTTPException(status_code=404, detail="Session not found")
    if session in current_user.enrolled_sessions: raise HTTPException(status_code=400, detail="Already enrolled")
    current_user.enrolled_sessions.append(session)
    db.commit()
    utils.log_activity(db, current_user.id, f"تسجيل: انضمام للجلسة {session_id}") # 👈 تم التصحيح
    return {"message": "Enrolled successfully!"}

@router.patch("/sessions/{session_id}/status")
def update_session_status(session_id: int, new_status: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if not any(role.role_name == "admin" for role in current_user.roles):
        raise HTTPException(status_code=403, detail="Admin only")
    session = db.query(models.SessionModel).filter(models.SessionModel.id == session_id).first()
    session.status = new_status
    db.commit()
    utils.log_activity(db, current_user.id, f"تغيير حالة الجلسة {session_id} إلى {new_status}") # 👈 تم التصحيح
    return {"message": "Status updated"}



@router.put("/categories/{category_id}", response_model=schemas.CategoryResponse)
def update_category(category_id: int, cat: schemas.CategoryCreate, db: Session = Depends(database.get_db)):
    db_cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db_cat.category_name = cat.category_name
    db.commit()
    db.refresh(db_cat)
    return db_cat

@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(database.get_db)):
    db_cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_cat)
    db.commit()
    return {"message": "Category deleted"}



# --- دالة "جلساتي المشتركة" (المخطط العلمي) ---
@router.get("/me/enrollments")
def get_my_enrollments(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # ربط 3 جداول لضمان جلب الاسم الحقيقي
    enrollments = db.query(models.Enrollment, models.SessionModel, models.User).join(
        models.SessionModel, models.Enrollment.session_id == models.SessionModel.id
    ).join(
        models.User, models.SessionModel.user_id == models.User.id
    ).filter(models.Enrollment.user_id == current_user.id).all()
    
    result = []
    for enroll, session, teacher in enrollments:
        result.append({
            "session_id": session.id,
            "session_title": session.title.split(" - ")[1] if " - " in session.title else session.title,
            "lecture_title": session.title.split(" - ")[0] if " - " in session.title else session.title,
            "teacher_name": f"{teacher.firstname} {teacher.lastname}", # 👈 الاسم الحقيقي هنا
            "date": session.date_time.strftime("%Y-%m-%d") if session.date_time else "غير محدد",
            "time": session.date_time.strftime("%H:%M") if session.date_time else "غير محدد",
            "duration": session.session_duration,
            "status": enroll.status,
            "meeting_link": session.meeting_link
        })
    return result

    # schemas.py
from pydantic import BaseModel
from datetime import date, time
from typing import List, Optional

class EnrollmentRequest(BaseModel):
    session_ids: List[int]

class EnrollmentStatusUpdate(BaseModel):
    user_id: int
    session_id: int
    status: str # 'approved' or 'rejected'

# ضيفي هذا الكود بنهاية ملف routers/sessions.py
from fastapi import HTTPException # تأكدي إنها مستوردة فوگ

@router.post("/enrollments/")
def create_enrollment(enrollment: schemas.EnrollmentStatusUpdate, db: Session = Depends(database.get_db)): # 👈 التعديل هنا ضفنا كلمة database.
    # 1. نتأكد إن الطالب ممقدم طلب سابقاً حتى لا تتكرر
    existing = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == enrollment.user_id,
        models.Enrollment.session_id == enrollment.session_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="لقد قمت بإرسال طلب سابقاً")

    # 2. إنشاء الطلب الجديد
    new_request = models.Enrollment(
        user_id=enrollment.user_id,
        session_id=enrollment.session_id,
        status="pending"
    )
    db.add(new_request)
    db.commit()
    return {"message": "تم استلام الطلب بنجاح"}

# ضيفي هذا الكود بنهاية routers/sessions.py



# 2. دالة تجيب الطلبات المعلقة للأستاذ (لصفحة TeacherRequests)
@router.get("/teacher/enrollments/pending")
def get_pending_requests(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # جلب الـ IDs الخاصة بجلسات هذا الأستاذ
    my_sessions_subquery = db.query(models.SessionModel.id).filter(models.SessionModel.user_id == current_user.id).subquery()
    
    # جلب الطلبات المعلقة (pending) اللي تخص هذي الجلسات
    pending_enrollments = db.query(models.Enrollment, models.SessionModel, models.User).join(
        models.SessionModel, models.Enrollment.session_id == models.SessionModel.id
    ).join(
        models.User, models.Enrollment.user_id == models.User.id
    ).filter(
        models.Enrollment.session_id.in_(my_sessions_subquery),
        models.Enrollment.status == "pending"
    ).all()

    result = []
    for enroll, session, student in pending_enrollments:
        result.append({
            "user_id": student.id,
            "session_id": session.id,
            "student_name": f"{student.firstname} {student.lastname}",
            "session_title": session.title,
            "date": session.date_time.split("T")[0] if session.date_time else "غير محدد"
        })
    return result

# 3. دالة لتحديث حالة الطلب (قبول/رفض) من قبل الأستاذ
class StatusUpdate(BaseModel): # إذا ما متعرفة فوگ
    user_id: int
    session_id: int
    status: str

@router.put("/enrollments/status")
def update_enrollment_status(status_data: StatusUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == status_data.user_id,
        models.Enrollment.session_id == status_data.session_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    enrollment.status = status_data.status
    db.commit()
    return {"message": "تم تحديث الحالة بنجاح"}

# ضيفي هذا الكود بنهاية routers/sessions.py
@router.get("/teacher/enrollments/approved")
def get_approved_students(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    my_sessions_subquery = db.query(models.SessionModel.id).filter(models.SessionModel.user_id == current_user.id).subquery()
    
    approved_enrollments = db.query(models.Enrollment, models.SessionModel, models.User).join(
        models.SessionModel, models.Enrollment.session_id == models.SessionModel.id
    ).join(
        models.User, models.Enrollment.user_id == models.User.id
    ).filter(
        models.Enrollment.session_id.in_(my_sessions_subquery),
        models.Enrollment.status == "approved"
    ).all()

    result = []
    for enroll, session, student in approved_enrollments:
        img_base64 = ""
        if student.profile_image:
            img_base64 = base64.b64encode(student.profile_image).decode('utf-8')
        result.append({
            "session_id": session.id,
            "student": {
                "id": student.id,
                "name": f"{student.firstname} {student.lastname}",
                "email": student.email,
                "bio": student.bio,
                # التصليح هنا: profile_image بدلاً من profile_image_url
                "image": img_base64
            }
        })
    return result

@router.get("/me/enrollments")
def get_my_enrollments(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # ربط 3 جداول: التسجيلات + الجلسات + المدرس (User)
    enrollments = db.query(models.Enrollment, models.SessionModel, models.User).join(
        models.SessionModel, models.Enrollment.session_id == models.SessionModel.id
    ).join(
        models.User, models.SessionModel.user_id == models.User.id
    ).filter(models.Enrollment.user_id == current_user.id).all()
    
    result = []
    for enroll, session, teacher in enrollments:
        # ترجمة الأيام للعربية
        days_ar = {"Monday": "الاثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", 
                   "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}
        
        result.append({
            "session_id": session.id,
            "session_title": session.title.split(" - ")[1] if " - " in session.title else session.title,
            "lecture_title": session.title.split(" - ")[0] if " - " in session.title else session.title,
            "teacher_name": f"{teacher.firstname} {teacher.lastname}", # جلب الاسم الحقيقي للمدرس
            "date": session.date_time.strftime("%Y-%m-%d") if session.date_time else "غير محدد",
            "time": session.date_time.strftime("%H:%M") if session.date_time else "00:00",
            "day": days_ar.get(session.date_time.strftime("%A"), "غير محدد") if session.date_time else "غير محدد",
            "duration": session.session_duration,
            "status": enroll.status,
            "meeting_link": session.meeting_link
        })
    return result

# D:\Graduation_project\KZ_backend\routers\sessions.py

@router.get("/me/sessions/")
def get_my_created_sessions(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # نجلب الجلسات اللي أنشأها هذا الأستاذ حصراً
    sessions = db.query(models.SessionModel).filter(models.SessionModel.user_id == current_user.id).all()
    
    result = []
    for s in sessions:
        # نحسب عدد المشتركين لكل جلسة
       result = []
    for s in sessions:
        # 👈 التعديل هنا: ضفنا شرط حتى نحسب بس الطلاب المقبولين فعلياً (approved)
        enroll_count = db.query(models.Enrollment).filter(
            models.Enrollment.session_id == s.id,
            models.Enrollment.status == "approved"
        ).count()
        
        result.append({
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "date_time": s.date_time,
            "duration": s.session_duration,
            "cover": s.cover_image_url,
            "enrollments_count": enroll_count # هذا الحقل راح نستخدمه بالفرونتند لمنع الحذف
        })
    return result

# تعديل دالة الحذف القديمة
@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    db_session = db.query(models.SessionModel).filter(models.SessionModel.id == session_id).first()
    if not db_session: 
        raise HTTPException(status_code=404, detail="المحاضرة غير موجودة")
    
    # التأكد من الملكية
    if db_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="غير مصرح لك بحذف هذه المحاضرة")

    # تشييك المشتركين (شرطك الأساسي)
    enroll_count = db.query(models.Enrollment).filter(models.Enrollment.session_id == session_id).count()
    if enroll_count > 0:
        raise HTTPException(status_code=400, detail="لا يمكن حذف المحاضرة لوجود طلاب مشتركين فيها!")

    db.delete(db_session)
    db.commit()
    utils.log_activity(db, current_user.id, f"حذف المحاضرة: {db_session.title}")
    return {"message": "تم الحذف بنجاح"}

# D:\Graduation_project\KZ_backend\routers\sessions.py

@router.post("/ratings/")
def create_session_rating(rating: schemas.RatingCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # 1. التأكد إن الطالب فعلاً مشترك ومقبول بالجلسة قبل لا يقيم
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.session_id == rating.session_id,
        models.Enrollment.user_id == current_user.id,
        models.Enrollment.status == "approved"
    ).first()

    if not enrollment:
        raise HTTPException(status_code=403, detail="لا يمكنك تقييم جلسة لست مشتركاً بها أو لم يتم قبولك فيها بعد.")

    # 2. التأكد إنه ما مقيم مسبقاً
    existing = db.query(models.Rating).filter(
        models.Rating.user_id == current_user.id, 
        models.Rating.session_id == rating.session_id
    ).first()
    
    if existing: 
        raise HTTPException(status_code=400, detail="لقد قمت بتقييم هذه الجلسة مسبقاً")
        
    # 3. حفظ التقييم بنجاح
    new_rating = models.Rating(
        user_id=current_user.id, 
        session_id=rating.session_id, 
        teacher_id=rating.teacher_id,
        session_rate=rating.session_rate, 
        teacher_rate=rating.teacher_rate
    )
    db.add(new_rating)
    db.commit()
    return {"message": "تم إرسال التقييم بنجاح"}

@router.get("/teacher/ratings-summary")
def get_teacher_feedback(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # جلب كافة التقييمات الخاصة بمحاضرات هذا الأستاذ حصراً
    results = db.query(models.Rating, models.User, models.SessionModel).join(
        models.User, models.Rating.user_id == models.User.id
    ).join(
        models.SessionModel, models.Rating.session_id == models.SessionModel.id
    ).filter(models.SessionModel.user_id == current_user.id).all()
    
    return [
        {
            "id": r.id,
            "student": f"{u.firstname} {u.lastname}",
            "lecture": s.title,
            "rate": r.rate,
            "comment": r.comment,
            "date": r.created_at.strftime("%Y-%m-%d")
        } for r, u, s in results
    ]


# D:\Graduation_project\KZ_backend\routers\sessions.py
from sqlalchemy import func
from datetime import datetime, timedelta
# D:\Graduation_project\KZ_backend\routers\sessions.py
@router.get("/teacher/dashboard-stats")
def get_teacher_stats(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # 1. حساب الطلاب المقبولين والطلبات المعلقة (كودج الأصلي)
    total_students = db.query(models.Enrollment).join(
        models.SessionModel, models.Enrollment.session_id == models.SessionModel.id
    ).filter(models.SessionModel.user_id == current_user.id, models.Enrollment.status == "approved").count()

    pending_requests = db.query(models.Enrollment).join(
        models.SessionModel, models.Enrollment.session_id == models.SessionModel.id
    ).filter(models.SessionModel.user_id == current_user.id, models.Enrollment.status == "pending").count()

    # 2. حساب متوسط التقييم (تفعيل المنطق الحقيقي)
    # 👈 جلب تقييمات هذا المعلم حصراً
    ratings = db.query(models.Rating).filter(models.Rating.teacher_id == current_user.id).all()
    avg_rating = 0
    rating_dist = [0, 0, 0, 0, 0]

    if ratings:
        # حساب المعدل
        total_sum = sum([(r.teacher_rate + r.session_rate) / 2 for r in ratings])
        avg_rating = round(total_sum / len(ratings), 1)
        # حساب التوزيع للمخطط
        for r in ratings:
            score = int(round((r.teacher_rate + r.session_rate) / 2))
            if 1 <= score <= 5:
                rating_dist[score - 1] += 1

    # 3. حساب نمو الطلاب (كودج الأصلي اللي يشتغل)
    growth_data = []
    has_created_at = hasattr(models.Enrollment, 'created_at')
    
    for i in range(6, -1, -1):
        target_date = (datetime.now() - timedelta(days=i)).date()
        query = db.query(models.Enrollment).join(
            models.SessionModel, models.Enrollment.session_id == models.SessionModel.id
        ).filter(
            models.SessionModel.user_id == current_user.id,
            models.Enrollment.status == "approved"
        )
        
        if has_created_at:
            query = query.filter(func.date(models.Enrollment.created_at) <= target_date)
            count = query.count()
        else:
            count = total_students if i == 0 else 0
            
        growth_data.append(count)

    return {
        "totalStudents": total_students,
        "pendingRequests": pending_requests,
        "avgRating": avg_rating, # 👈 هسة راح يرجع رقم
        "enrollmentGrowth": growth_data,
        "ratingDistribution": rating_dist # 👈 وهسة المخطط راح يتحدث
    }
# ضيفي هذا الكود بنهاية ملف routers/sessions.py
@router.get("/teacher/enrollments/history")
def get_history_requests(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # جلب الـ IDs الخاصة بجلسات هذا الأستاذ
    my_sessions_subquery = db.query(models.SessionModel.id).filter(models.SessionModel.user_id == current_user.id).subquery()
    
    # جلب الطلبات اللي تمت معالجتها (ليست قيد الانتظار)
    history_enrollments = db.query(models.Enrollment, models.SessionModel, models.User).join(
        models.SessionModel, models.Enrollment.session_id == models.SessionModel.id
    ).join(
        models.User, models.Enrollment.user_id == models.User.id
    ).filter(
        models.Enrollment.session_id.in_(my_sessions_subquery),
        models.Enrollment.status != "pending"
    ).all()

    result = []
    for enroll, session, student in history_enrollments:
        # تأكدي إن التاريخ يتحول لنص إذا كان موجود
        date_str = "غير محدد"
        if session.date_time:
            date_str = session.date_time.strftime("%Y-%m-%d") if hasattr(session.date_time, 'strftime') else str(session.date_time).split("T")[0]
            
        result.append({
            "user_id": student.id,
            "session_id": session.id,
            "student_name": f"{student.firstname} {student.lastname}",
            "session_title": session.title,
            "date": date_str,
            "status": enroll.status # يفيدنا حتى نلون الطلب بالفرونت إند
        })
    return result


@router.post("/comments/")
def add_comment(comment: schemas.CommentCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    new_comment = models.Comment(
        session_id=comment.session_id,
        user_id=current_user.id,
        content=comment.content,
        parent_id=comment.parent_id
    )
    db.add(new_comment)
    db.commit()
    return {"message": "تم إضافة التعليق بنجاح"}

@router.get("/sessions/{session_id}/details")
def get_session_full_details(session_id: int, db: Session = Depends(database.get_db)):
    session = db.query(models.SessionModel).filter(models.SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
    
    teacher = db.query(models.User).filter(models.User.id == session.user_id).first()
    
    # 1. جلب التقييمات
    ratings = db.query(models.Rating).filter(models.Rating.session_id == session_id).all()
    avg_session_rate = sum([r.session_rate for r in ratings]) / len(ratings) if ratings else 0
    avg_teacher_rate = sum([r.teacher_rate for r in ratings]) / len(ratings) if ratings else 0
    # أول شي نحول الجلسة لقاموس (Dictionary)
    session_data = schemas.SessionResponse.model_validate(session).dict()
    
    # 👈 هسة نضيف حقل الكفر داخل هذا القاموس حصراً
    session_data["cover"] = session.cover_image_url.split('/')[-1] if session.cover_image_url else 'default.png'
    session_data["display_cover"] = session_data["cover"] # للضمان
    # 2. جلب التعليقات مع الردود
    comments = db.query(models.Comment).filter(models.Comment.session_id == session_id, models.Comment.parent_id == None).order_by(models.Comment.created_at.desc()).all()
    
    def format_comment(c):
        import base64
        img_base64 = None
        if c.user.profile_image:
            img_base64 = f"data:image/jpeg;base64,{base64.b64encode(c.user.profile_image).decode()}"
        return {
            "id": c.id, "content": c.content, "created_at": c.created_at,
            "user_id": c.user.id, "user_name": f"{c.user.firstname} {c.user.lastname}",
            "user_image": img_base64,
            "replies": [format_comment(reply) for reply in c.replies]
        }
        
    return {
        "session": session_data, # 👈 هسة الـ cover صار جوة الـ session
        "teacher_name": f"{teacher.firstname} {teacher.lastname}",
        "teacher_id": teacher.id,
        "avg_session_rating": round(avg_session_rate, 1),
        "avg_teacher_rating": round(avg_teacher_rate, 1),
        "ratings_count": len(ratings),
        "comments": [format_comment(c) for c in comments],
        
    }

@router.post("/ratings/")
def create_session_rating(rating: schemas.RatingCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    existing = db.query(models.Rating).filter(models.Rating.user_id == current_user.id, models.Rating.session_id == rating.session_id).first()
    if existing: raise HTTPException(status_code=400, detail="لقد قمت بتقييم هذه الجلسة مسبقاً")
        
    new_rating = models.Rating(
        user_id=current_user.id, session_id=rating.session_id, teacher_id=rating.teacher_id,
        session_rate=rating.session_rate, teacher_rate=rating.teacher_rate
    )
    db.add(new_rating)
    db.commit()
    return {"message": "تم إرسال التقييم بنجاح"}