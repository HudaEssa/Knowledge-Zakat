from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Table, Text,LargeBinary
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# جداول الربط (Many-to-Many)
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

session_categories = Table('session_categories', Base.metadata,
    Column('session_id', Integer, ForeignKey('sessions.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String)
    lastname = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    bio = Column(Text, nullable=True)
    birthday_date = Column(Date, nullable=True)
   # profile_image_url = Column(String, nullable=True)
    profile_image = Column(LargeBinary, nullable=True)
    is_active = Column(Boolean, default=True)
    
    
    
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    # ربط المستخدم بالجلسات اللي مسجل بيها
    enrolled_sessions = relationship("SessionModel", secondary="enrollments", back_populates="students")

class SessionModel(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    session_duration = Column(Integer, nullable=False)
    date_time = Column(DateTime, nullable=False)
    meeting_link = Column(String, nullable=True)
    status = Column(String, default="scheduled")
    cover_image_url = Column(Text, nullable=True)
    
    categories = relationship("Category", secondary=session_categories, back_populates="sessions")
    students = relationship("User", secondary="enrollments", back_populates="enrolled_sessions")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, unique=True, nullable=False)
    sessions = relationship("SessionModel", secondary=session_categories, back_populates="categories")

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String, unique=True, nullable=False)
    users = relationship("User", secondary=user_roles, back_populates="roles")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    details = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class TeacherApproval(Base):
    __tablename__ = "teacher_approvals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cv_link = Column(String, nullable=True)
    phone = Column(String, nullable=True) # 👈 ضيفي هذا السطر
    status = Column(String, default="pending")

class Enrollment(Base):
    __tablename__ = "enrollments"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), primary_key=True)
    status = Column(String, default="pending")

class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # الطالب
    session_id = Column(Integer, ForeignKey("sessions.id")) # الجلسة
    teacher_id = Column(Integer, ForeignKey("users.id")) # المعلم
    session_rate = Column(Integer) # تقييم الجلسة من 1-5
    teacher_rate = Column(Integer) # تقييم المعلم من 1-5
    created_at = Column(DateTime, default=datetime.utcnow)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True) # هذا يفيدنا حتى نسوي "رد على تعليق"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    session = relationship("SessionModel")
    # علاقة التعليقات ببعضها (الردود)
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Comment", back_populates="replies", remote_side=[id])