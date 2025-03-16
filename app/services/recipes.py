from app.utils.convert import encode_image, decode_image
from app.repositories import repo
from app.utils.errors import *
from io import StringIO
import csv
import app.schemas.ingredients as sching
import app.schemas.recipes as schrec
import app.schemas.users as schuser
import app.schemas.tags as schtag
import app.db.models as models


def get_recipe_response(recipe, user=None):
    author = repo.get_recipe_author(recipe.id)
    return schrec.RecipeResponse(
        id=recipe.id,
        tags=[
            schtag.Tag(
                id=tag.id,
                name=tag.name,
                color='#E26C2D',
                slug=tag.slug
            ) for tag in repo.get_recipe_tags(recipe.id)
        ],
        author=schuser.Author(
            id=author.id,
            email=author.email,
            username=author.username,
            first_name=author.first_name,
            last_name=author.last_name,
            is_subscribed=repo.is_subscribed(user.id, recipe) if user else False,
        ),
        ingredients=[
            sching.Ingredient(
                id=ingredient[0].id,
                name=ingredient[0].name,
                measurement_unit=ingredient[0].measurement_unit,
                amount=ingredient[1]
            ) for ingredient in repo.get_recipe_ingredients(recipe.id)
        ],
        # is_favorited=any(favourite.id == recipe.id for favourite in user.favourites) if user else False,
        is_favorited=False,
        is_in_shopping_cart=False,
        # is_in_shopping_cart=any(item.id == recipe.id for item in user.shopping_cart) if user else False,  # TODO: remake
        name=recipe.name,
        image=encode_image(recipe.image),
        text=recipe.text,
        cooking_time=recipe.cooking_time
    )


def get_download_shopping_cart(user_id: int):
    items = repo.get_shopping_cart(user_id)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Название", "Количество", "Единица измерения"])

    for item in items:
        writer.writerow([item.name, item.amount, item.measurement_unit])
    return output


def get_recipes(page: int,
                limit: int,
                is_favorited: int,
                is_in_shopping_cart: int,
                author: models.User,
                tags: list[str],
                url: str,
                user: models.User):
    author_id = -1
    if author:
        author_id = author.id
    tags_list = []
    if tags:
        tags_list = tags
    total, recipes = repo.get_recipes(page, limit, is_favorited, is_in_shopping_cart, author_id, tags_list, user.id)
    results = []
    for recipe in recipes:
        results.append(get_recipe_response(recipe, user))

    base_url = str(url).split("?")[0]
    next_url = (
        f"{base_url}?page={page + 1}&limit={limit}"
        if (page * limit) < total else None
    )
    previous_url = (
        f"{base_url}?page={page - 1}&limit={limit}"
        if page > 1 else None
    )
    return schrec.RecipePaginationResponse(
        count=total,
        next=next_url,
        previous=previous_url,
        results=results
    )


def get_recipe(recipe_id: int, user: models.User):
    recipe = repo.get_recipe(recipe_id)
    if not recipe:
        raise recipe_not_found_err
    return get_recipe_response(recipe, user)


def create_recipe(recipe_data: schrec.RecipeCreate, user_id: int):
    image = decode_image(recipe_data.image)
    recipe = models.Recipe(
        name=recipe_data.name,
        image=image,
        cooking_time=recipe_data.cooking_time,
        text=recipe_data.text,
        author_id=user_id
    )
    recipe = repo.save_recipe(recipe)

    ingredients = []
    for ingredient in recipe_data.ingredients:
        db_ingredient = models.RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            amount=ingredient.amount
        )
        ingredients.append(db_ingredient)
    repo.save_ingredients_recipe(recipe.id, ingredients)

    ok = repo.save_tags_by_id_recipe(recipe, recipe_data.tags)
    if not ok:
        raise tag_not_found_err

    return get_recipe_response(recipe)


def update_recipe(id: int, recipe_update: schrec.RecipeUpdate, user: models.User):
    recipe = repo.get_recipe(id)
    if not recipe:
        raise recipe_not_found_err
    if recipe.author_id != user.id:
        raise permission_denied_err

    recipe.name = recipe.name
    recipe.text = recipe.text
    recipe.cooking_time = recipe.cooking_time
    recipe.image = decode_image(recipe.image) if recipe.image != "" else None

    ingredients = []
    for ingredient in recipe.ingredients:
        db_ingredient = models.RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            amount=ingredient.amount
        )
        ingredients.append(db_ingredient)
    repo.save_ingredients_recipe(recipe.id, ingredients)
    ok = repo.save_tags_by_id_recipe(recipe, recipe_update.tags)
    if not ok:
        raise tag_not_found_err

    recipe = repo.update_recipe(recipe)
    return get_recipe_response(recipe, user)


def add_favourite_recipe(recipe_id: int, user: models.User):
    recipe = repo.get_recipe(recipe_id)
    if not recipe:
        raise recipe_not_found_err
    repo.add_favourite_recipe(recipe, user)


def delete_favourite_recipe(recipe_id: int, user: models.User):
    repo.delete_favourite_recipe(user.id, recipe_id)


def add_to_shopping_cart(recipe_id: int, user: models.User):
    recipe = repo.get_recipe(recipe_id)
    if not recipe:
        raise recipe_not_found_err
    exists = repo.is_recipe_in_shopping_cart(recipe_id, user.id)
    if exists:
        raise already_in_shopping_cart_err
    repo.add_recipe_to_shopping_cart(recipe_id, user.id)
    return schrec.RecipeShortDataResponse(
            id=recipe.id,
            name=recipe.name,
            image=encode_image(recipe.image),
            cooking_time=recipe.cooking_time
        )


def remove_from_shopping_cart(recipe_id: int, user: models.User):
    exists = repo.is_recipe_in_shopping_cart(recipe_id, user.id)
    if exists:
        raise havent_recipe_in_shopping_cart_err
    repo.delete_recipe_from_shopping_cart(recipe_id, user.id)
