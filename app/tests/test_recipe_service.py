import unittest
import app.services.recipes as svc
from app.utils.errors import *
from app.schemas.recipes import RecipeResponse, Tag
from app.schemas.users import Author
from app.schemas.ingredients import Ingredient
import app.db.models as models


class MockRepo:
    def __init__(self):
        self.recipes = []
        self.users = []
        self.favourite_calls = []
        self.deleted_favourite_calls = []
        self.shopping_cart = {}

    def get_recipe(self, recipe_id: int):
        if len(self.recipes) > 0:
            for val in self.recipes:
                if val.id == recipe_id:
                    return val
        return None

    def add_favourite_recipe(self, recipe: models.Recipe, user: models.User):
        self.favourite_calls.append((recipe, user))

    def get_user_by_id(self, user_id: int):
        if len(self.users) > 0:
            for val in self.users:
                if val.id == user_id:
                    return val
        return None

    def get_recipe(self, id: int):
        pass


class DummyRecipe:
    def __init__(self, id, name, image=b'', cooking_time=30, text="", author=None):
        self.id = id
        self.name = name
        self.image = image
        self.cooking_time = cooking_time
        self.text = text
        self.ingredients = []
        self.tags = []
        self.author = author

    def __str__(self):
        return f"Recipe(id={self.id} name='{self.name}' cooking_time={self.cooking_time})"


class DummyUser:
    def __init__(self, id, email="example@example.com", username="dummy", first_name="Dummy", last_name="Dummy"):
        self.id = id
        self.email = email
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.favourites = []
        self.subscriptions = []

    def __str__(self):
        return f"User(id={self.id} email='{self.email}' username='{self.username}')"


class DummyIngredientModel:
    def __init__(self, id, name, measurement_unit):
        self.id = id
        self.name = name
        self.measurement_unit = measurement_unit


class DummyIngredient:
    def __init__(self, id, ingredient, amount):
        self.id = id
        self.amount = amount
        self.ingredient = ingredient


class DummyTag:
    def __init__(self, id, name, color, slug):
        self.id = id
        self.name = name
        self.color = color
        self.slug = slug



class TestRecipeService(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MockRepo()
        svc.repo = self.mock_repo

        self.user = DummyUser(id=1)
        self.author = DummyUser(id=2,
                                email="author@example.com",
                                username="author",
                                first_name="Author",
                                last_name="Authorov")
        self.tags = [DummyTag(id=1, name="Test tag", color="#FFFFFF", slug="test")]
        ingredient = DummyIngredientModel(id=1, name="Bread", measurement_unit="kg")
        self.ingredients = [DummyIngredient(id=1, ingredient=ingredient, amount=1)]
        self.recipe = DummyRecipe(id=1,
                                  name="Test recipe",
                                  image=b'test_image',
                                  text="Test text field",
                                  author=self.author)
        for ingredient in self.ingredients:
            self.recipe.ingredients.append(ingredient)
        for tag in self.tags:
            self.recipe.tags.append(tag)
        self.mock_repo.recipes.append(self.recipe)

    def test_add_favourite_recipe_success(self):
        self.mock_repo.users.append(self.user)
        self.mock_repo.get_recipe = lambda x: self.recipe
        svc.add_favourite_recipe(self.recipe.id, self.user)
        l = len(self.mock_repo.favourite_calls)
        exp = 1
        self.assertEqual(l, exp, f"Got {l} Expected {exp}")

        pair = self.mock_repo.favourite_calls[0]
        exp = (self.recipe, self.user)
        self.assertEqual(exp, pair, f"Got {pair[0]}, {pair[1]} Expected {exp[0]}, {exp[1]}")

    def test_add_favourite_recipe_not_found(self):
        self.mock_repo.recipe = []
        with self.assertRaises(Error) as e:
            svc.add_favourite_recipe(self.recipe.id, self.user)
        exp_err = recipe_not_found_err
        self.assertEqual(exp_err, e.exception)

    def test_add_favourite_recipe_none_user(self):
        with self.assertRaises(Error) as e:
            svc.add_favourite_recipe(self.recipe.id, None)
        exp_err = user_not_found_err
        self.assertEqual(exp_err, e.exception)

    def test_add_favourite_recipe_bad_user(self):
        with self.assertRaises(Error) as e:
            svc.add_favourite_recipe(self.recipe.id, self.user)
        exp_err = user_not_found_err
        self.assertEqual(exp_err, e.exception)

    def test_add_favourite_recipe_2_requests(self):
        self.mock_repo.users.append(self.user)
        svc.add_favourite_recipe(self.recipe.id, self.user)
        with self.assertRaises(Error) as e:
            svc.add_favourite_recipe(self.recipe.id, self.user)
        exp_err = already_in_favourite_err
        self.assertEqual(exp_err, e.exception)

    def test_get_recipe_success(self):
        self.mock_repo.get_recipe = lambda x: self.recipe
        from app.utils.convert import encode_image
        expected = RecipeResponse(
            id=self.recipe.id,
            tags=[
                Tag(
                    id=tag.id,
                    name=tag.name,
                    color=tag.color,
                    slug=tag.slug
                ) for tag in self.tags
            ],
            author=Author(
                id=self.author.id,
                email=self.author.email,
                username=self.author.username,
                first_name=self.author.first_name,
                last_name=self.author.last_name,
                is_subscribed=False
            ),
            ingredients=[
                Ingredient(
                    id=ingredient.id,
                    name=ingredient.ingredient.name,
                    measurement_unit=ingredient.ingredient.measurement_unit,
                    amount=ingredient.amount
                ) for ingredient in self.ingredients
            ],
            is_favorited=False,
            is_in_shopping_cart=False,
            name=self.recipe.name,
            image=encode_image(self.recipe.image),
            text=self.recipe.text,
            cooking_time=self.recipe.cooking_time
        )
        recipe = svc.get_recipe(self.recipe.id, self.user)
        self.assertEqual(expected, recipe, "Invalid result")

    def test_get_recipe_fail(self):
        self.mock_repo.get_recipe = lambda x: None
        with self.assertRaises(Error) as e:
            svc.get_recipe(self.recipe.id, self.user)
        exp_err = recipe_not_found_err
        self.assertEqual(exp_err, e.exception)