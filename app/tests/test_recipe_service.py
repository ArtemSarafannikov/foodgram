import unittest
import app.services.recipes as svc
from app.utils.errors import *
import app.db.models as models


class MockRepo:
    def __init__(self):
        self.recipe = None
        self.user = None
        self.favourite_calls = []
        self.deleted_favourite_calls = []
        self.shopping_cart = {}

    def get_recipe(self, recipe_id: int):
        if self.recipe and self.recipe.id == recipe_id:
            return self.recipe
        return None

    def add_favourite_recipe(self, recipe: models.Recipe, user: models.User):
        self.favourite_calls.append((recipe, user))

    def get_user_by_id(self, user_id: int):
        if self.user and self.user.id == user_id:
            return self.user
        return None


class DummyRecipe(models.Recipe):
    def __init__(self, id, name, image=b'', cooking_time=30, text="", author_id=None):
        self.id = id
        self.name = name
        self.image = image
        self.cooking_time = cooking_time
        self.text = text
        self.author_id = author_id
        self.ingredients = []
        self.tags = []
        self.author = None

    def __str__(self):
        return f"Recipe(id={self.id} name='{self.name}' cooking_time={self.cooking_time})"


class DummyUser(models.User):
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


class TestRecipeService(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MockRepo()
        svc.repo = self.mock_repo

        self.user = DummyUser(id=1)
        self.recipe = DummyRecipe(id=1, name="Test recipe", image=b'test_image', text="Test text field")
        self.mock_repo.recipe = self.recipe

    def test_add_favourite_recipe_success(self):
        self.mock_repo.user = self.user
        svc.add_favourite_recipe(self.recipe.id, self.user)
        l = len(self.mock_repo.favourite_calls)
        exp = 1
        self.assertEqual(l, exp, f"Got {l} Expected {exp}")

        pair = self.mock_repo.favourite_calls[0]
        exp = (self.recipe, self.user)
        self.assertEqual(pair, exp, f"Got {pair[0]}, {pair[1]} Expected {exp[0]}, {exp[1]}")

    def test_add_favourite_recipe_not_found(self):
        self.mock_repo.recipe = None
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
        self.mock_repo.user = self.user
        svc.add_favourite_recipe(self.recipe.id, self.user)
        with self.assertRaises(Error) as e:
            svc.add_favourite_recipe(self.recipe.id, self.user)
        exp_err = already_in_favourite_err
        self.assertEqual(exp_err, e.exception)
