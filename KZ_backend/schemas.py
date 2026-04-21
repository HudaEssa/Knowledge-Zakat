from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, date
from datetime import date, time
from sqlmodel import Field

# --- User Schemas ---
class RoleResponse(BaseModel):
    id: int
    role_name: str
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    password: str = Field(..., min_length=8)
    bio: Optional[str] = None
    birthday_date: Optional[date] = None


class UserUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[EmailStr] = None 
    old_password: Optional[str] = None  # 👈 إضافة هذا
    new_password: Optional[str] = None  # 👈 إضافة هذا
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    birthday_date: Optional[date] = None
class LoginInput(BaseModel):
    email: EmailStr
    password: str

# schemas.py
import base64
from pydantic import validator

class UserResponse(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: EmailStr
    is_active: bool
    bio: Optional[str] = None
    roles: List[RoleResponse] = []
    # غيري هذا الحقل ليكون نصاً لاستلام الـ Base64
    profile_image: Optional[str] = None 

    @validator("profile_image", pre=True)
    def convert_binary_to_base64(cls, v):
        if isinstance(v, bytes):
           
            return f"data:image/png;base64,{base64.b64encode(v).decode()}"
        return v

    class Config:
        from_attributes = True

# --- Content Schemas -------------------------------------------------------------------
class CategoryCreate(BaseModel):
    category_name: str

class CategoryResponse(CategoryCreate):
    id: int
    class Config:
        from_attributes = True

# في ملف schemas.py
class SessionCreate(BaseModel):
    title: str
    description: str
    session_duration: int
    date_time: datetime # 👈 تأكدي إن الاسم date_time مو created_at
    category_ids: List[int] = [] # 👈 الباكيند مالتج يسوي لها .pop()
    
    # ⚠️ هذني الحقول جانت ناقصة وهي اللي تسبب الـ 422
    meeting_link: Optional[str] = None
    cover_image_url: Optional[str] = None
    status: str = "scheduled" 
# schemas.py
class SessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    session_duration: Optional[int] = None
    date_time: Optional[datetime] = None
    category_ids: Optional[List[int]] = None
    meeting_link: Optional[str] = None # تأكد من إضافة هذا
    cover_image_url: Optional[str] = None # تأكد من إضافة هذا
    

# في ملف schemas.py

class SessionResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    session_duration: int  # 👈 تأكد إنها موجودة هنا
    date_time: datetime    # 👈 تأكد إنها موجودة هنا
    teacher_name: Optional[str] = None 
    meeting_link: Optional[str] = None
    cover_image_url: Optional[str] = None 
    categories: List[CategoryResponse] = []
    teacher_id: Optional[int] = None 
    teacher_name: Optional[str] = None
    display_cover: Optional[str] = None

    class Config:
        from_attributes = True
# --- Interaction Schemas ------------------------------------------------------------------
class RatingCreate(BaseModel):
    session_id: int
    rate: int
    comment: Optional[str] = None

class RatingResponse(BaseModel):
    id: int
    session_id: int
    rate: int
    comment: Optional[str]
    student_name: str
    session_title: str
    created_at: datetime

    class Config:
        from_attributes = True

class ApprovalCreate(BaseModel):
    cv_link: str
    phone: Optional[str] = None # 👈 ضيفي هذا السطر

class ApprovalResponse(ApprovalCreate):
    id: int
    user_id: int
    status: str
    class Config:
        from_attributes = True

 # --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None
    email: Optional[str] = None

# --- Activity Log Schemas ---

class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    details: Optional[str] = None 
    timestamp: datetime

    class Config:
        from_attributes = True

# إذا ردتي تطلعين اسم المستخدم وية اللوگ (حتى الأدمن يعرف منو سوى الحركة بدون ما يدوخ بالـ ID)
class ActivityLogWithUserResponse(ActivityLogResponse):
    # هنا نفترض إن اليوزر مربوط بمودل ActivityLog بـ relationship اسمها user
    user: Optional[UserResponse] = None



class EnrollmentRequest(BaseModel):
    session_ids: List[int]

class EnrollmentStatusUpdate(BaseModel):
    user_id: int
    session_id: int
    status: str # 'approved' or 'rejected'

class EnrollmentCreate(BaseModel):
    user_id: int
    session_id: int
    status: str = "pending"

# --- Comments & Ratings Schemas ---
class CommentCreate(BaseModel):
    session_id: int
    content: str
    parent_id: Optional[int] = None

class CommentResponse(BaseModel):
    id: int
    session_id: int
    user_id: int
    content: str
    parent_id: Optional[int]
    created_at: datetime
    user_name: str
    user_image: Optional[str] = None
    replies: List['CommentResponse'] = [] 

    class Config:
        from_attributes = True

# ⚠️ ملاحظة: إذا عندج RatingCreate قديمة امسحيها وحطي هاي بمكانها
class RatingCreate(BaseModel):
    session_id: int
    teacher_id: int
    session_rate: int
    teacher_rate: int