from app.repositories import repo
from app.utils.errors import Error
from fastapi import status


def get_ingredients(name: str):
    return repo.get_ingredients_by_name(name)


def get_ingredient(id: int):
    ingredient = repo.get_ingredient_by_id(id)
    if not ingredient:
        raise Error(status.HTTP_404_NOT_FOUND, "Ingredient not found")
    return ingredient
