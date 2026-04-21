# D:\Graduation_project\KZ_backend\utils.py
from passlib.context import CryptContext
import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def log_activity(db, user_id, details):
    try:
        new_log = models.ActivityLog(user_id=user_id, details=details)
        db.add(new_log)
        db.commit()
    except Exception as e:
        print(f"Log Error: {e}")
