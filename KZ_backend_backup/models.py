"""
Knowledge Zakat — Database Models
=================================
Refactored to use SQLModel as the primary ORM layer (per project rule).
We only fall back to raw SQLAlchemy primitives when SQLModel does not
expose them — currently just `LargeBinary` for the profile-image BLOB.

Architectural notes:
- All link tables for many-to-many relationships are explicit SQLModel
  classes. This is the recommended SQLModel pattern (over implicit
  Table objects) and lets us add columns later — `Enrollment` already
  carries an extra `status` column for exactly this reason.
- Public class names are identical to the previous SQLAlchemy version
  (User, SessionModel, Category, Role, Enrollment, ...) so the routers
  and Svelte frontend keep working with no API changes.
- We declare link tables BEFORE the entities that reference them via
  `link_model=`. SQLModel can't accept a forward-reference / lambda
  here, so the file is ordered link-tables -> entities.
- `datetime.utcnow` is deprecated in Python 3.12+; we use a small helper
  that returns a tz-aware UTC timestamp instead.
"""

from datetime import datetime, date, timezone
from typing import List, Optional

from sqlmodel import SQLModel, Field, Relationship
# `LargeBinary` has no SQLModel-native shorthand — this is the
# documented exception to the "SQLModel first" rule.
from sqlalchemy import Column, LargeBinary

import uuid
def _utcnow() -> datetime:
    """Timezone-aware UTC now. Replaces the deprecated `datetime.utcnow()`."""
    return datetime.now(timezone.utc)


# ===========================================================================
# Link tables (declared first, so the entity classes can reference them
# directly via `link_model=...`).
# ===========================================================================

class UserRole(SQLModel, table=True):
    """Pure association between users and roles (no extra columns)."""
    __tablename__ = "user_roles"

    user_id: Optional[int] = Field(
        default=None, foreign_key="users.id", primary_key=True
    )
    role_id: Optional[int] = Field(
        default=None, foreign_key="roles.id", primary_key=True
    )


class SessionCategory(SQLModel, table=True):
    """Pure association between sessions and categories."""
    __tablename__ = "session_categories"

    session_id: Optional[int] = Field(
        default=None, foreign_key="sessions.id", primary_key=True
    )
    category_id: Optional[int] = Field(
        default=None, foreign_key="categories.id", primary_key=True
    )


class Enrollment(SQLModel, table=True):
    """
    Association *with extra data*: this row also carries the enrollment
    status (pending/approved/rejected) and the creation timestamp used
    for the dashboard growth chart. Composite primary key on
    (user_id, session_id) prevents duplicate requests.
    """
    __tablename__ = "enrollments"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", primary_key=True)
    status: str = Field(default="pending")
    notification_seen: bool = Field(default=False)


# ===========================================================================
# Core entities
# ===========================================================================

class User(SQLModel, table=True):
    """
    Application user. A single user can hold one or more roles
    (student / teacher / admin) via the UserRole link table.
    """
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    firstname: str
    lastname: str
    # `unique=True` + `index=True` enforce that no two accounts share an
    # email at the database level. Email lookup during login is also
    # accelerated by the index.
    email: str = Field(unique=True, index=True)
    hashed_password: str
    bio: Optional[str] = None
    birthday_date: Optional[date] = None

    # Profile image is stored as a binary BLOB. SQLModel doesn't have a
    # first-class binary field, so we declare the SQLAlchemy column
    # directly via `sa_column`.
    profile_image: Optional[bytes] = Field(
        default=None, sa_column=Column(LargeBinary, nullable=True)
    )

    # `is_active=False` means the admin has deactivated this account.
    # The login flow and `get_current_user` both check this flag.
    is_active: bool = Field(default=True)

    # Many-to-many relationships
    roles: List["Role"] = Relationship(
        back_populates="users", link_model=UserRole
    )
    enrolled_sessions: List["SessionModel"] = Relationship(
        back_populates="students", link_model=Enrollment
    )


class SessionModel(SQLModel, table=True):
    """
    A teaching session ("lecture") created by a teacher.
    The class name `SessionModel` (not `Session`) deliberately avoids
    a clash with SQLAlchemy's `Session` and matches every existing
    import elsewhere in the codebase.
    """
    __tablename__ = "sessions"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    title: str = Field(nullable=False)
    description: str = Field(nullable=False)
    session_duration: int = Field(nullable=False)
    date_time: datetime = Field(nullable=False)
    meeting_link: Optional[str] = None
    status: str = Field(default="scheduled")
    cover_image_url: Optional[str] = None
    # Capacity cap. NULL = unlimited (the default). When set, the
    # enrollment endpoint must refuse new requests once the count of
    # accepted enrollments reaches this number.
    student_limit: Optional[int] = Field(default=None, nullable=True)

    categories: List["Category"] = Relationship(
        back_populates="sessions", link_model=SessionCategory
    )
    students: List["User"] = Relationship(
        back_populates="enrolled_sessions", link_model=Enrollment
    )


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    category_name: str = Field(unique=True, nullable=False)

    sessions: List["SessionModel"] = Relationship(
        back_populates="categories", link_model=SessionCategory
    )


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    role_name: str = Field(unique=True, nullable=False)

    users: List["User"] = Relationship(
        back_populates="roles", link_model=UserRole
    )


# ===========================================================================
# Auxiliary tables
# ===========================================================================

class ActivityLog(SQLModel, table=True):
    """
    Append-only audit trail. We log every security-relevant action
    (login, register, password change, enrollment changes, etc.).
    """
    __tablename__ = "activity_logs"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id")
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=_utcnow)


class TeacherApproval(SQLModel, table=True):
    """A pending request from a student to be promoted to teacher."""
    __tablename__ = "teacher_approvals"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    cv_link: Optional[str] = None
    phone: Optional[str] = None
    status: str = Field(default="pending")  # pending / approved / rejected


class Rating(SQLModel, table=True):
    """A student's rating of a session AND its teacher (one row covers both)."""
    __tablename__ = "ratings"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id")        # student
    session_id: int = Field(foreign_key="sessions.id")
    teacher_id: int = Field(foreign_key="users.id")
    session_rate: int   # 1..5 — validated at the schema layer
    teacher_rate: int   # 1..5
    created_at: datetime = Field(default_factory=_utcnow)


class Comment(SQLModel, table=True):
    """
    Threaded comments on a session. `parent_id` allows nested replies.
    Self-referential relationships need explicit `remote_side`, which
    SQLModel exposes via `sa_relationship_kwargs`.
    """
    __tablename__ = "comments"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    session_id: int = Field(foreign_key="sessions.id", nullable=False)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    parent_id: Optional[int] = Field(default=None, foreign_key="comments.id")
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=_utcnow)

    parent: Optional["Comment"] = Relationship(
        back_populates="replies",
        sa_relationship_kwargs={"remote_side": "Comment.id"},
    )
    replies: List["Comment"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    # Convenience relationship to the comment author so router code can
    # write `comment.user.firstname` without an extra query.
    user: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Comment.user_id==User.id",
            "foreign_keys": "[Comment.user_id]",
        }
    )



class UploadedFile(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    data: bytes
    mime_type: str