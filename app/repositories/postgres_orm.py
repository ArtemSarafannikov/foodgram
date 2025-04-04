from app.db.session import SessionLocal, DATABASE_URL
from sqlalchemy import select, text
from app.schemas.recipes import ShoppingCart, IngredientSchema
from app.db.models import *
import psycopg2

class PostgresRepo:
    def get_session(self):
        db = psycopg2.connect(DATABASE_URL)
        return db

    def get_users_by_email_username(self, email: str, username: str) -> list[User]:
        query = """SELECT id, email, username, first_name, last_name, hashed_password, avatar
                 FROM users WHERE email = %s OR username = %s"""
        result = None
        with self.get_session() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (email, username))
                res = cur.fetchall()
                if len(res) != 0:
                    result = []
                    for r in res:
                        result.append(User(id=r[0],
                                      email=r[1],
                                      username=r[2],
                                      first_name=r[3],
                                      last_name=r[4],
                                      hashed_password=r[5],
                                      avatar=r[6]))
        return result

    def get_user_by_id(self, id: int) -> User:
        query = """SELECT id, email, username, first_name, last_name, hashed_password, avatar
                 FROM users WHERE id=%s"""
        result = None
        with self.get_session() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (id,))
                res = cur.fetchone()
                if res:
                    result = User(id=res[0],
                                       email=res[1],
                                       username=res[2],
                                       first_name=res[3],
                                       last_name=res[4],
                                       hashed_password=res[5],
                                       avatar=res[6])
        return result

    def save_user(self, user: User) -> User:
        query = """INSERT INTO users (email, username, first_name, last_name, hashed_password, avatar)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id"""
        with self.get_session() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user.email, user.username, user.first_name, user.last_name, user.hashed_password, user.avatar))
                user.id = cur.fetchone()[0]
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

    def get_recipe_author(self, recipe_id: int) -> User:
        query = """SELECT users.*
                     FROM recipes
                     JOIN users ON recipes.author_id = users.id
                     WHERE recipes.id = %s"""
        result = None
        with self.get_session() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (recipe_id,))
                res = cur.fetchone()
                if res:
                   result = User(id=res[0],
                                 email=res[1],
                                 username=res[2],
                                 first_name=res[3],
                                 last_name=res[4],
                                 hashed_password=res[5],
                                 avatar=res[6])
        return result

    def get_recipe_tags(self, recipe_id: int) -> list[Tag]:
        query = """SELECT id, name, slug
                         FROM tags
                         JOIN recipe_tags ON tags.id = recipe_tags.tag_id
                         WHERE recipe_id = %s"""
        result = None
        with self.get_session() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (recipe_id,))
                res = cur.fetchall()
                if len(res) != 0:
                    result = []
                    for r in res:
                        result.append(Tag(id=r[0],
                                          name=r[1],
                                          slug=r[2]))
        return result

    def get_recipe_ingredients(self, recipe_id: int) -> list[tuple[Ingredient, int]]:
        query = """SELECT ingredients.*, amount
                         FROM ingredients
                         JOIN recipe_ingredients ON ingredients.id = recipe_ingredients.ingredient_id
                         WHERE recipe_id = %s"""
        result = None
        with self.get_session() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (recipe_id,))
                res = cur.fetchall()
                if len(res) != 0:
                    result = []
                    for r in res:
                        elem = (Ingredient(id=r[0], name=r[1], measurement_unit=r[2]), r[3])
                        result.append(elem)
        return result

    def is_subscribed(self, user_id: int, recipe: Recipe) -> bool:
        query = """SELECT * FROM recipes
                    JOIN user_subscriptions ON recipes.author_id = user_subscriptions.author_id
                    WHERE user_id = %s AND recipe_id = %s"""
        with self.get_session() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id, recipe.id))
                res = cur.fetchall()
                return len(res) != 0
        return False

    def save_recipe(self, recipe: Recipe) -> Recipe:
        query = """INSERT INTO recipes (name, image, cooking_time, text, author_id)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id"""
        with self.get_session() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (recipe.name, recipe.image, recipe.cooking_time, recipe.text, recipe.author_id))
                recipe.id = cur.fetchone()[0]
        return recipe

    def save_ingredients_recipe(self, recipe_id: int, ingredients: list[RecipeIngredient]):
        del_query = """DELETE FROM recipe_ingredients WHERE recipe_id=%s"""
        query = """INSERT INTO recipe_ingredients (recipe_id, ingredient_id, amount)
                                            VALUES (%s, %s, %s)"""
        with self.get_session() as conn:
            with conn.cursor() as cur:
                for ingredient in ingredients:
                    cur.execute(del_query, (recipe_id,))
                    cur.execute(query, (recipe_id, ingredient.ingredient_id, ingredient.amount))

    def save_tags_by_id_recipe(self, recipe: Recipe, tags: list[int]) -> bool:
        del_query = """DELETE FROM recipe_tags WHERE recipe_id=%s"""
        query = """INSERT INTO recipe_tags (recipe_id, tag_id)
                                                    VALUES (%s, %s)"""
        with self.get_session() as conn:
            with conn.cursor() as cur:
                for tag in tags:
                    cur.execute(del_query, (recipe.id,))
                    cur.execute(query, (recipe.id, tag))
        return True

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
