from datetime import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, database, utils, oauth2 
from oauth2 import check_admin_role
import shutil
from pathlib import Path
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(tags=["Users"])

# حددي مسار فولدر الصور
UPLOAD_DIR = Path("static/profile_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 1. (Register)
@router.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = utils.hash(user.password) # تأكدي ان اسم الدالة hash في utils
    new_user = models.User(
        firstname=user.firstname, lastname=user.lastname, 
        email=user.email, hashed_password=hashed_pwd, bio=user.bio, birthday_date=user.birthday_date
    )
    
    student_role = db.query(models.Role).filter(models.Role.role_name == "student").first()
    if student_role:
        new_user.roles.append(student_role)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    utils.log_activity(db, new_user.id, "مستخدم جديد سجل بالنظام (register)")
    return new_user

# 2. (Login) - تم التعديل ليطابق oauth2 الجديد
@router.post("/token")
def login(login_data: schemas.LoginInput, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user or not utils.verify(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    utils.log_activity(db, user.id, "قام المستخدم بتسجيل الدخول للنظام")

    # نستخدم الدالة من oauth2 ونرسل الايميل كـ sub
    access_token = oauth2.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# 3. جلب بياناتي (Me)
@router.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(oauth2.get_current_user)): 
    return current_user

# 4. جلب كل المستخدمين
@router.get("/users/", response_model=List[schemas.UserResponse])
def read_all_users(db: Session = Depends(database.get_db)):
    return db.query(models.User).all()

# 5. تحديث بيانات (Update) - تم تبديل utils بـ oauth2
@router.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.firstname: db_user.firstname = user_update.firstname
    if user_update.lastname: db_user.lastname = user_update.lastname
    if user_update.bio: db_user.bio = user_update.bio
    
    db.commit()
    db.refresh(db_user)
    utils.log_activity(db, user_id, "قام المستخدم بتحديث بيانات بروفايله")
    return db_user

# 6. حذف مستخدم (Delete) - تم تبديل utils بـ oauth2
@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.id != user_id: 
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    utils.log_activity(db, user_id, "حذف حسابه نهائياً من النظام")
    return {"message": "User deleted successfully"}



from fastapi import UploadFile, File, HTTPException
import shutil
import os
@router.post("/me/upload-image", response_model=schemas.UserResponse) # 👈 لازم نحدد الـ Schema هنا
async def upload_profile_image(
    file: UploadFile = File(...), 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
):
    image_data = await file.read()
    current_user.profile_image = image_data # خزن الـ BLOB
    
    db.commit() 
    # 👈 السطر المنقذ: هذا السطر يجيب الـ roles من الداتابيز ويخلي السيفيلت يعرف إنك طالبة
    db.refresh(current_user) 
    
    return current_user


# 9. طلب الانضمام لجلسة (Enrollment Request) - تم التصحيح
@router.post("/enrollments/request", status_code=status.HTTP_201_CREATED)
def request_enrollment(
    data: dict, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user) # 👈 تم التبديل هنا
):
    session_id = data.get('session_id')
    
    db_session = db.query(models.SessionModel).filter(models.SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")

    # استخدام كلاس Enrollment الكابيتال
    existing_enroll = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == current_user.id,
        models.Enrollment.session_id == session_id
    ).first()
    
    if existing_enroll:
        raise HTTPException(status_code=400, detail="لقد أرسلت طلباً لهذه الجلسة مسبقاً")

    new_enroll = models.Enrollment(
        user_id=current_user.id,
        session_id=session_id,
        status="pending" 
    )

    try:
        db.add(new_enroll)
        db.commit()
        db.refresh(new_enroll)
        utils.log_activity(db, current_user.id, f"طلب الطالب انضمام للجلسة رقم {session_id}")
        return {"message": "تم إرسال طلب الانضمام بنجاح، بانتظار موافقة الأستاذ ⏳"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="فشل في إرسال الطلب")

@router.post("/logout")
def logout(current_user: models.User = Depends(oauth2.get_current_user), db: Session = Depends(database.get_db)):
    utils.log_activity(db, current_user.id, "المستخدم سجل خروج من النظام")
    return {"message": "Logged out"}




# routers/users.py

@router.get("/teacher/enrollments/pending")
def get_teacher_pending_enrollments(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # ربط الجداول (Join) لجلب اسم الطالب وعنوان الجلسة الخاصة بهذا المعلم حصراً
    results = db.query(models.Enrollment, models.User.firstname, models.SessionModel.title)\
        .join(models.SessionModel, models.Enrollment.session_id == models.SessionModel.id)\
        .join(models.User, models.Enrollment.user_id == models.User.id)\
        .filter(models.SessionModel.user_id == current_user.id, models.Enrollment.status == "pending")\
        .all()
    
    return [
        {"user_id": e.user_id, "session_id": e.session_id, "student_name": fn, "session_title": title} 
        for e, fn, title in results
    ]

@router.patch("/enrollments/update")
def update_enrollment_status(data: dict, db: Session = Depends(database.get_db)):
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == data.get('user_id'),
        models.Enrollment.session_id == data.get('session_id')
    ).first()
    if enrollment:
        enrollment.status = data.get('status')
        db.commit()
    return {"message": "تم التحديث"}

# routers/users.py

@router.get("/enrollments/my-sessions/", response_model=List[schemas.SessionResponse])
def get_my_enrolled_sessions(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # جلب الجلسات التي تكون حالة التسجيل فيها 'approved' للطالب الحالي
    sessions = db.query(models.SessionModel)\
        .join(models.Enrollment, models.SessionModel.id == models.Enrollment.session_id)\
        .filter(models.Enrollment.user_id == current_user.id, models.Enrollment.status == "approved")\
        .all()
    
    return sessions

UPLOAD_DIR = "pics"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/sessions/upload-cover")
async def upload_session_cover(file: UploadFile = File(...)):
    # 1. التأكد من نوع الملف
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="الملف يجب أن يكون صورة")

    # 2. توليد اسم فريد للملف
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 3. حفظ الملف في فولدر pics
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="فشل في حفظ الصورة")

    # 4. نرجع اسم الملف فقط للفرونتند
    return {"cover_url": unique_filename}    

# D:\Graduation_project\KZ_backend\routers\users.py

from fastapi.responses import Response # تأكد من استيراد Response

@router.get("/users/{user_id}/profile_image")
def get_user_profile_image(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.profile_image:
        raise HTTPException(status_code=404, detail="الصورة غير موجودة")
    
    # إرسال بيانات الـ BLOB مباشرة وتحديد نوع المحتوى كصورة
    return Response(content=user.profile_image, media_type="image/jpeg")

# D:\Graduation_project\KZ_backend\routers\admin.py


import base64
@router.get("/teachers/")
def get_all_teachers(db: Session = Depends(database.get_db)):
    teachers = db.query(models.User).join(models.user_roles).join(models.Role).filter(models.Role.role_name == "teacher").all()
    result = []
    for t in teachers:
        ratings = db.query(models.Rating).filter(models.Rating.teacher_id == t.id).all()
        avg_rate = sum([r.teacher_rate for r in ratings]) / len(ratings) if ratings else 0
        img_base64 = f"data:image/jpeg;base64,{base64.b64encode(t.profile_image).decode()}" if t.profile_image else None
            
        result.append({
            "id": t.id, "name": f"{t.firstname} {t.lastname}", "bio": t.bio or "معلم في منصة زكاة العلم",
            "image": img_base64, "avg_rating": round(avg_rate, 1), "ratings_count": len(ratings)
        })
    return result

@router.get("/teachers/{teacher_id}/profile")
def get_teacher_profile(teacher_id: int, db: Session = Depends(database.get_db)):
    teacher = db.query(models.User).filter(models.User.id == teacher_id).first()
    if not teacher: raise HTTPException(status_code=404, detail="المعلم غير موجود")

    # جلب جلسات المعلم
    sessions = db.query(models.SessionModel).filter(models.SessionModel.user_id == teacher_id).all()
    
    formatted_sessions = []
    for s in sessions:
        ratings = db.query(models.Rating).filter(models.Rating.session_id == s.id).all()
        avg_rate = sum([r.session_rate for r in ratings]) / len(ratings) if ratings else 0
        formatted_sessions.append({
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "cover": s.cover_image_url,
            "avg_rating": round(avg_rate, 1)
        })

    import base64
    img_base64 = f"data:image/jpeg;base64,{base64.b64encode(teacher.profile_image).decode()}" if teacher.profile_image else None

    # تقييم المعلم الكلي
    teacher_ratings = db.query(models.Rating).filter(models.Rating.teacher_id == teacher_id).all()
    avg_teacher_rate = sum([r.teacher_rate for r in teacher_ratings]) / len(teacher_ratings) if teacher_ratings else 0

    return {
        "id": teacher.id,
        "name": f"{teacher.firstname} {teacher.lastname}",
        "bio": teacher.bio or "لا توجد نبذة تعريفية",
        "image": img_base64,
        "avg_rating": round(avg_teacher_rate, 1),
        "sessions_count": len(sessions),
        "sessions": formatted_sessions
    }

@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user_profile(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    
    # 1. 👈 نشيك إذا المستخدم هو "أدمن"
    is_admin = any(role.role_name == "admin" for role in current_user.roles)
    
    # 2. 👈 نعدل الشرط: إذا مو صاحب الحساب "و" مو أدمن.. اهنا نمنعه
    if current_user.id != user_id and not is_admin:
        raise HTTPException(status_code=403, detail="غير مصرح لك بتعديل هذا الحساب")

    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    # تحديث البيانات (firstname, lastname, bio)
    if user_update.firstname: db_user.firstname = user_update.firstname
    if user_update.lastname: db_user.lastname = user_update.lastname
    if user_update.bio: db_user.bio = user_update.bio
    
    # 👈 تشفير الباسورد إذا المستخدم كتب واحد جديد بالـ Modal
    if user_update.password and user_update.password.strip() != "":
        db_user.hashed_password = utils.hash(user_update.password)

    db.commit()
    db.refresh(db_user)
    return db_user