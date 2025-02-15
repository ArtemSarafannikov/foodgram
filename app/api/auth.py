from fastapi import APIRouter, HTTPException
from app.utils.errors import Error
import app.services.auth as service
import app.schemas.auth as schemes


router = APIRouter()


@router.post('/token/login/', response_model=schemes.Token)
def login(login_request: schemes.LoginRequest):
    try:
        access_token = service.login(login_request)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message,
        )
    return {"auth_token": access_token, "token_type": "Bearer"}


@router.post("/token/logout/")
def logout():
    return {"message": "successful"}
