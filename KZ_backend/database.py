from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# connection with DB
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:12345678huda@localhost/knowledgeZakat"


engine = create_engine(SQLALCHEMY_DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# .الأساس (Base) - أي جدول نسويه لازم يورث من هذا الأساس
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()