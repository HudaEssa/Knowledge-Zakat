from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import database, models, schemas, utils, oauth2

router = APIRouter(tags=['Authentication'])

@router.post("/login")
def login(login_data: schemas.LoginInput, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Email or Password")

    if not utils.verify(login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Email or Password")
    
    # التأكد إذا الحساب محظور من الأدمن
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your account is deactivated by Admin")

    access_token = oauth2.create_access_token(data={"sub": user.email})
    utils.log_activity(db, user.id, "User logged in successfully")
    
    return {"access_token": access_token, "token_type": "bearer"}