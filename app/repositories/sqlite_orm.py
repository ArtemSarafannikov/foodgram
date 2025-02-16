from app.db.session import SessionLocal
from sqlalchemy import select, text
from app.utils.errors import Error
from app.schemas.recipes import ShoppingCart, IngredientSchema
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

    def get_shopping_cart(self, user_id: id) -> list[ShoppingCart]:
        with engine.connect() as connection:
            items = connection.execute(text(f'''SELECT i.name, SUM(ri.amount) amount, i.measurement_unit
                                            FROM shopping_cart sc
                                            NATURAL JOIN recipe_ingredients ri
                                            JOIN ingredients i ON ri.ingredient_id=i.id
                                            WHERE sc.user_id={user_id}
                                            GROUP BY i.id'''))
        return items

    def get_recipes(self, page: int,
                    limit: int,
                    is_favorited: int,
                    is_in_shopping_cart: int,
                    author_id: int,
                    tags: list[str],
                    user_id: int) -> tuple[int, list[Recipe]]:
        db = self.get_session()
        query = db.query(Recipe)
        if author_id != -1:
            query = query.filter(Recipe.author_id == author_id)
        if len(tags) > 0:
            query = query.filter(Recipe.tags.any(Tag.slug.in_(tags)))
        if is_favorited == 1:
            query = query.filter(Recipe.favourites.any(id=user_id))
        if is_in_shopping_cart == 1:
            query = query.filter(Recipe.shopping_cart.any(id=user_id))
        total = query.count()
        recipes = query.offset((page - 1) * limit).limit(limit).all()
        db.close()
        return total, recipes

    def get_recipe(self, id: int):
        db = self.get_session()
        recipe = db.query(Recipe).filter(Recipe.id == id).first()
        db.close()
        return recipe

    def save_recipe(self, recipe: Recipe) -> Recipe:
        db = self.get_session()
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        db.close()
        return recipe

    def save_ingredients_recipe(self, recipe_id: int, ingredients: list[RecipeIngredient]):
        db = self.get_session()
        db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe_id).delete()
        for ingredient in ingredients:
            db.add(ingredient)
        db.commit()
        db.close()

    def save_tags_by_id_recipe(self, recipe: Recipe, tags: list[int]) -> bool:
        db = self.get_session()
        db.execute(recipe_tags.delete().where(recipe_tags.c.recipe_id == recipe.id))
        result = True
        for tag_id in tags:
            db_tag = self.get_tag(tag_id)
            if not db_tag:
                result = False
                break
            else:
                recipe.tags.append(db_tag)
        if result:
            db.commit()
        db.close()
        return result

    def update_recipe(self, recipe: Recipe):
        db = self.get_session()
        db.commit()
        db.refresh(recipe)
        db.close()
        return recipe

    def add_favourite_recipe(self, recipe: Recipe, user: User):
        db = self.get_session()
        recipe.favourites.append(user)
        db.commit()
        db.close()

    def delete_favourite_recipe(self, user_id: int, recipe_id: int):
        db = self.get_session()
        db.execute(favourite_recipes.delete()
                   .where((favourite_recipes.c.user_id == user_id) & (
                favourite_recipes.c.recipe_id == recipe_id)))
        db.commit()
        db.close()

    def is_recipe_in_shopping_cart(self, recipe_id: int, user_id: int) -> bool:
        db = self.get_session()
        exists = db.execute(select(shopping_cart)
                            .where((shopping_cart.c.user_id == user_id) & (
                shopping_cart.c.recipe_id == recipe_id))
                            ).fetchone()
        db.close()
        return exists is None

    def add_recipe_to_shopping_cart(self, recipe_id: int, user_id: int):
        db = self.get_session()
        db_cart = shopping_cart.insert().values(user_id=user_id, recipe_id=recipe_id)
        db.execute(db_cart)
        db.commit()
        db.close()

    def delete_recipe_from_shopping_cart(self, recipe_id: int, user_id: int):
        db = self.get_session()
        db_cart = (shopping_cart.delete()
                   .where(
            (shopping_cart.c.user_id == user_id) & (shopping_cart.c.recipe_id == recipe_id)))
        db.execute(db_cart)
        db.commit()
        db.close()
