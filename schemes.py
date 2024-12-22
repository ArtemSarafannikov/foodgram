from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    auth_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str
    first_name: str
    last_name: str


class UserGet(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    avatar: str


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


class ResetPassword(BaseModel):
    email: str


class AvatarUpload(BaseModel):
    avatar: str
