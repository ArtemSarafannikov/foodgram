from app.repositories.sqlite_orm import SQLiteRepo
from app.utils.errors import Error
from app.core.security import verify_password, create_access_token
from fastapi import status
import app.schemas.auth as schemes

repo = SQLiteRepo()


def login(login_request: schemes.LoginRequest):
    user = repo.get_users_by_email_username(login_request.email, "")
    error = Error(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    if len(user) == 0:
        raise error
    user = user[0]
    if not verify_password(login_request.password, user.hashed_password):
        raise error
    access_token = create_access_token(data={"sub": user.email})
    return access_token
