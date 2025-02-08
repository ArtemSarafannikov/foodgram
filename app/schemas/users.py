from pydantic import BaseModel, EmailStr
from typing import List, Optional


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


class Author(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    is_subscribed: bool


class UserResponse(BaseModel):
    email: str
    id: int
    username: str
    first_name: str
    last_name: str
    is_subscribed: bool
    avatar: Optional[str]


class UserPaginationResponse(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[UserResponse]
