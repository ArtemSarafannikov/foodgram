from app.db.session import SessionLocal
from app.db.models import *


class SQLiteRepo:
    def get_session(self):
        db = SessionLocal()
        return db

    def get_users_by_email_username(self, email: str, username: str):
        db = self.get_session()
        result = (db.query(User).
              filter((User.email == email) | (User.username == username)).all())
        db.close()
        return result

    def save_user(self, user: User) -> User:
        db = self.get_session()
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()
        return user

    def update_user(self, user_db: User, new_user: User) -> None:
        db = self.get_session()
        for field, value in user_db.__dict__.items():
            setattr(user_db, field, getattr(new_user, field))
        db.commit()
        db.close()
