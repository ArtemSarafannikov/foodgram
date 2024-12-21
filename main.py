from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal, get_db
from utility import *

import models
import schemes

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/token/login/')

async def get_current_user(token: str = Depends(oauth2_scheme), db: SessionLocal = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise credentials_exception
    return user

@app.post('/api/auth/token/login/', response_model=schemes.Token)
def login(login_request: schemes.LoginRequest, db: SessionLocal = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == login_request.email).first()
    if not user or not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"auth_token": access_token, "token_type": "Bearer"}


@app.get("/api/users/me/")
def get_current_user_profile(current_user: models.User = Depends(get_current_user)):
    return current_user
