from fastapi import APIRouter, Depends, HTTPException, status
from app.db.session import SessionLocal, get_db
from app.core.security import verify_password, create_access_token
import app.schemas.auth as schemes
import app.db.models as models


router = APIRouter()


@router.post('/token/login/', response_model=schemes.Token)
def login(login_request: schemes.LoginRequest, db: SessionLocal = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == login_request.email).first()
    if not user or not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"auth_token": access_token, "token_type": "Bearer"}


@router.post("/token/logout/")
def logout():
    return {"message": "successful"}
