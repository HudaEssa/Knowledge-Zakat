"""
Pydantic schemas (request bodies / response models).

Cleanups over the previous version:
- Migrated to Pydantic v2 idioms: `field_validator` (the v1 `validator`
  is deprecated and will be removed) and `model_config = ConfigDict(...)`
  instead of nested `class Config`.
- Removed duplicate definitions of `RatingCreate`, `EnrollmentRequest`,
  etc. — the old file declared the same classes twice, with the second
  definition silently shadowing the first.
- `UserUpdate` now exposes BOTH `old_password` and `new_password`. The
  router validates `old_password` against the stored hash before
  applying the change. The previous implementation had `old_password`
  in the schema but never checked it, which let any authenticated user
  reset their own password without proving they knew the old one.
- `password` and rating fields now have explicit length / range checks.
- Response schemas keep the same field names and JSON shape so the
  Svelte frontend continues to work without modification.
"""

import base64
from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

class RoleResponse(BaseModel):
    id: int
    role_name: str
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date


class User(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: EmailStr
    phone: Optional[str] = None
    bio: Optional[str] = None
    birthday_date: Optional[date] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True 
class UserCreate(BaseModel):
    firstname: str = Field(..., min_length=1, max_length=80)
    lastname: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    # Minimum 8 chars matches the previous policy. We could tighten this
    # (require digit + symbol) but that's a UX call for the team.
    password: str = Field(..., min_length=8, max_length=128)
    bio: Optional[str] = Field(default=None, max_length=2000)
    birthday_date: Optional[date] = None


class UserUpdate(BaseModel):
    firstname: Optional[str] = Field(default=None, min_length=1, max_length=80)
    lastname: Optional[str] = Field(default=None, min_length=1, max_length=80)
    email: Optional[EmailStr] = None
    bio: Optional[str] = Field(default=None, max_length=2000)
    birthday_date: Optional[date] = None
    profile_image_url: Optional[str] = None

    # Password change is opt-in: BOTH old and new must be supplied.
    # The router enforces that pairing — see users.py.
    old_password: Optional[str] = None
    new_password: Optional[str] = Field(default=None, min_length=8, max_length=128)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: EmailStr
    is_active: bool
    bio: Optional[str] = None
    roles: List[RoleResponse] = []
    # The DB stores raw bytes; when serialising a response we convert to
    # a data: URL on the fly so the Svelte frontend can drop it straight
    # into an <img> tag.
    profile_image: Optional[str] = None

    @field_validator("profile_image", mode="before")
    @classmethod
    def _binary_to_data_url(cls, v):
        if isinstance(v, (bytes, bytearray)):
            return f"data:image/png;base64,{base64.b64encode(v).decode()}"
        return v

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

class CategoryCreate(BaseModel):
    category_name: str = Field(..., min_length=1, max_length=120)


class CategoryResponse(CategoryCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    session_duration: int = Field(..., gt=0, le=600)  # minutes; sane bounds
    date_time: datetime
    category_ids: List[int] = []
    meeting_link: Optional[str] = None
    cover_image_url: Optional[str] = None
    status: str = "scheduled"
    # Capacity cap. None = unlimited. When set, the enrollment endpoint
    # refuses new requests once the count of accepted enrollments
    # reaches this number.
    student_limit: Optional[int] = Field(default=None, ge=1, le=10000)


class SessionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    session_duration: Optional[int] = Field(default=None, gt=0, le=600)
    date_time: Optional[datetime] = None
    category_ids: Optional[List[int]] = None
    meeting_link: Optional[str] = None
    cover_image_url: Optional[str] = None
    # Teachers can lift/lower the cap later. Sending null explicitly
    # would unset the cap (back to unlimited), so the router must
    # distinguish "field missing" from "field == None". `model_dump
    # (exclude_unset=True)` already handles this.
    student_limit: Optional[int] = Field(default=None, ge=1, le=10000)


class SessionResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    session_duration: int
    date_time: datetime
    meeting_link: Optional[str] = None
    cover_image_url: Optional[str] = None
    categories: List[CategoryResponse] = []
    teacher_id: Optional[int] = None
    teacher_name: Optional[str] = None
    display_cover: Optional[str] = None
    # Capacity fields exposed to the frontend so it can show
    # "X / Y seats" or "Full" badges. `accepted_count` is computed
    # at response time, not stored.
    student_limit: Optional[int] = None
    accepted_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Ratings
# ---------------------------------------------------------------------------

class RatingCreate(BaseModel):
    """A student's rating of a session and its teacher (1..5 each)."""
    session_id: int
    teacher_id: int
    session_rate: int = Field(..., ge=1, le=5)
    teacher_rate: int = Field(..., ge=1, le=5)


class RatingResponse(BaseModel):
    id: int
    session_id: int
    rate: int
    comment: Optional[str] = None
    student_name: str
    session_title: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Teacher approvals
# ---------------------------------------------------------------------------

class ApprovalCreate(BaseModel):
    cv_link: str
    phone: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    user_id: int
    status: str
    phone: Optional[str] = None
    # هذي الحقول نحتاجها حتى تظهر بالـ Modal مال الأدمن
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    birthday_date: Optional[date] = None
    
    # تحويل الـ BLOB (الـ CV) إلى Base64 آلياً
    cv_link: Optional[str] = None

    @field_validator("cv_link", mode="before")
    @classmethod
    def _binary_to_data_url(cls, v):
        if isinstance(v, (bytes, bytearray)):
            # نحوله لـ Data URL حتى الـ Svelte يحطه بـ <img> مباشرة
            return f"data:image/png;base64,{base64.b64encode(v).decode()}"
        return v

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Auth tokens
# ---------------------------------------------------------------------------

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None
    email: Optional[str] = None


# ---------------------------------------------------------------------------
# Activity log
# ---------------------------------------------------------------------------

class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    details: Optional[str] = None
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


class ActivityLogWithUserResponse(ActivityLogResponse):
    user: Optional[UserResponse] = None


# ---------------------------------------------------------------------------
# Enrollments
# ---------------------------------------------------------------------------

class EnrollmentRequest(BaseModel):
    session_id: int


class EnrollmentStatusUpdate(BaseModel):
    user_id: int
    session_id: int
    status: str  # 'approved' or 'rejected'

    @field_validator("status")
    @classmethod
    def _status_must_be_known(cls, v: str) -> str:
        if v not in {"pending", "approved", "rejected"}:
            raise ValueError("status must be pending, approved, or rejected")
        return v


class EnrollmentCreate(BaseModel):
    user_id: int
    session_id: int
    status: str = "pending"


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

class CommentCreate(BaseModel):
    session_id: int
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[int] = None


class CommentResponse(BaseModel):
    id: int
    session_id: int
    user_id: int
    content: str
    parent_id: Optional[int] = None
    created_at: datetime
    user_name: str
    user_image: Optional[str] = None
    replies: List["CommentResponse"] = []

    model_config = ConfigDict(from_attributes=True)


# Pydantic v2 needs an explicit rebuild call to resolve the forward
# reference inside `replies: List["CommentResponse"]`.
CommentResponse.model_rebuild()

class ImageUploadResponse(BaseModel):
    cover_url: str


class AdminCreate(BaseModel):
    firstname: str = Field(..., min_length=1, max_length=80)
    lastname: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8, max_length=128)    

class PaginatedUsersResponse(BaseModel):
    items: List[UserResponse]
    total: int