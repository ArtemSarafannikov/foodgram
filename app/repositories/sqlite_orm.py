from app.db.session import SessionLocal
from app.db.models import *


class SQLiteRepo:
    def get_session(self):
        db = SessionLocal()
        return db

    def get_users_by_email_username(self, email: str, username: str) -> list[User]:
        db = self.get_session()
        result = (db.query(User).
              filter((User.email == email) | (User.username == username)).all())
        db.close()
        return result

    def get_user_by_id(self, id: int) -> User:
        db = self.get_session()
        req_user = db.query(User).filter(User.id == id).first()
        db.close()
        return req_user

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

    def get_count_users(self) -> int:
        db = self.get_session()
        total = db.query(User).count()
        db.close()
        return total

    def get_users_pagination(self, limit: int, offset: int):
        db = self.get_session()
        users = db.query(User).offset(offset).limit(limit).all()
        db.close()
        return users

    def add_subscription(self, subscriber: User, author: User) -> None:
        db = self.get_session()
        subscriber.subscriptions.append(author)
        db.commit()
        db.close()

    def delete_subscribe(self, subscriber: User, author: User):
        db = self.get_session()
        db.execute(user_subscriptions.delete().
                   where((user_subscriptions.c.user_id == subscriber.id) &
                         (user_subscriptions.c.author_id == author.id)))
        db.commit()
        db.close()

    def get_tags(self) -> list[Tag]:
        db = self.get_session()
        tags = db.query(Tag).all()
        db.close()
        return tags

    def get_tag(self, id: int) -> Tag:
        db = self.get_session()
        tag = db.query(Tag).filter(Tag.id == id).first()
        db.close()
        return tag

    def get_ingredients_by_name(self, name: str) -> list[Ingredient]:
        db = self.get_session()
        ingredients = db.query(Ingredient).filter(Ingredient.name.like(f"%{name}%")).all()
        db.close()
        return ingredients

    def get_ingredient_by_id(self, id: int) -> Ingredient:
        db = self.get_session()
        ingredient = db.query(Ingredient).filter(Ingredient.id == id).first()
        db.close()
        return ingredient
