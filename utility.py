from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional

import secrets
import base64
import string

SECRET_KEY = "41e9d135b735a3a92831c7918f011c0048bb927e9412ce3452b77d8096c6e331"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def decode_image(b64_avatar):
    '''
    Переводит картинку base64 в байтовый формат
    :param b64_avatar:
    :return:
    '''
    return base64.b64decode(b64_avatar.split(',')[1])


def encode_image(byte_avatar):
    '''
    Переводит байты картинки в формат base64
    :param byte_avatar:
    :return:
    '''
    avatar = base64.b64encode(byte_avatar).decode("utf-8") if byte_avatar else ''
    return f"data:image/png;base64,{avatar}" if avatar else ''
