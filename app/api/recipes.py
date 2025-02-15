from fastapi import APIRouter, Depends, status, HTTPException, Request, Response, Query
from sqlalchemy import select, text
from io import StringIO
from typing import List, Optional
from app.utils.convert import encode_image, decode_image
from app.db.session import SessionLocal, get_db, engine
from app.core.security import get_current_user
import app.schemas.ingredients as sching
import app.schemas.users as schuser
import app.schemas.recipes as schrec
import app.schemas.tags as schtag
import app.db.models as models
import csv

router = APIRouter()


def get_recipe_response(recipe, user=None):
    return schrec.RecipeResponse(
        id=recipe.id,
        tags=[
            schtag.Tag(
                id=tag.id,
                name=tag.name,
                color='#E26C2D',
                slug=tag.slug
            ) for tag in recipe.tags
        ],
        author=schuser.Author(
            id=recipe.author.id,
            email=recipe.author.email,
            username=recipe.author.username,
            first_name=recipe.author.first_name,
            last_name=recipe.author.last_name,
            is_subscribed=any(subscription.id == recipe.author.id for subscription in user.subscriptions) if user else False
        ),
        ingredients=[
            sching.Ingredient(
                id=ingredient.id,
                name=ingredient.ingredient.name,
                measurement_unit=ingredient.ingredient.measurement_unit,
                amount=ingredient.amount
            ) for ingredient in recipe.ingredients
        ],
        is_favorited=any(favourite.id == recipe.id for favourite in user.favourites) if user else False,
        is_in_shopping_cart=False,
        name=recipe.name,
        image=encode_image(recipe.image),
        text=recipe.text,
        cooking_time=recipe.cooking_time
    )


@router.get("/download_shopping_cart/")
def download_shopping_cart(current_user: models.User = Depends(get_current_user)):
    with engine.connect() as connection:
        items = connection.execute(text(f'''SELECT i.name, SUM(ri.amount) amount, i.measurement_unit
                                        FROM shopping_cart sc
                                        NATURAL JOIN recipe_ingredients ri
                                        JOIN ingredients i ON ri.ingredient_id=i.id
                                        WHERE sc.user_id={current_user.id}
                                        GROUP BY i.id'''))

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Название", "Количество", "Единица измерения"])

    for item in items:
        writer.writerow([item.name, item.amount, item.measurement_unit])

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=shopping_cart.csv"
    return response


@router.get("/", response_model=schrec.RecipePaginationResponse)
def get_recipes(
        page: int = 1,
        limit: int = 6,
        is_favorited: int = 0,
        is_in_shopping_cart: int = 0,
        author: Optional[int] = None,
        tags: Optional[List[str]] = Query(None),
        request: Request = None,
        db: SessionLocal = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Recipe)
    if author:
        query = query.filter(models.Recipe.author_id == author)
    if tags:
        query = query.filter(models.Recipe.tags.any(models.Tag.slug.in_(tags)))
    if is_favorited == 1:
        query = query.filter(models.Recipe.favourites.any(id=current_user.id))
    if is_in_shopping_cart == 1:
        query = query.filter(models.Recipe.shopping_cart.any(id=current_user.id))

    total = query.count()
    recipes = query.offset((page - 1) * limit).limit(limit).all()

    results = []
    for recipe in recipes:
        results.append(get_recipe_response(recipe, current_user))

    base_url = str(request.url).split("?")[0]
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


@router.get("/{id}/", response_model=schrec.RecipeResponse)
def get_recipe(id: int, db: SessionLocal = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == id).first()
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail="No recipe with this id"
        )
    return get_recipe_response(recipe, current_user)


@router.post("/")
def create_recipe(recipe_data: schrec.RecipeCreate,
                  current_user: models.User = Depends(get_current_user),
                  db: SessionLocal = Depends(get_db)):
    image = decode_image(recipe_data.image)
    db_recipe = models.Recipe(
        name=recipe_data.name,
        image=image,
        cooking_time=recipe_data.cooking_time,
        text=recipe_data.text,
        author_id=current_user.id
    )
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)

    for ingredient in recipe_data.ingredients:
        db_ingredient = models.RecipeIngredient(
            recipe_id=db_recipe.id,
            ingredient_id=ingredient.id,
            amount=ingredient.amount
        )
        db.add(db_ingredient)

    for tag_id in recipe_data.tags:
        db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
        if not db_tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        db_recipe.tags.append(db_tag)
    db.commit()

    return get_recipe_response(db_recipe)


@router.patch("/{id}/")
def update_recipe(id: int,
                  recipe: schrec.RecipeUpdate,
                  current_user: models.User = Depends(get_current_user),
                  db: SessionLocal = Depends(get_db)):
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == id).first()
    if not db_recipe:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found"
        )
    if db_recipe.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Haven't permission"
        )

    db_recipe.name = recipe.name
    db_recipe.text = recipe.text
    db_recipe.cooking_time = recipe.cooking_time
    db_recipe.image = decode_image(recipe.image) if recipe.image != "" else None

    db.query(models.RecipeIngredient).filter(models.RecipeIngredient.recipe_id == id).delete()
    for ingredient in recipe.ingredients:
        db_ingredient = models.RecipeIngredient(
            recipe_id=db_recipe.id,
            ingredient_id=ingredient.id,
            amount=ingredient.amount
        )
        db.add(db_ingredient)

    db.execute(models.recipe_tags.delete().where(models.recipe_tags.c.recipe_id == id))
    for tag_id in recipe.tags:
        db.execute(models.recipe_tags.insert().values(recipe_id=id, tag_id=tag_id))

    db.commit()
    db.refresh(db_recipe)
    return get_recipe_response(db_recipe, current_user)


@router.post("/{id}/favorite/")
def add_to_favourite(id: int,
                     current_user: models.User = Depends(get_current_user),
                     db: SessionLocal = Depends(get_db)):
    # favourite = models.favourite_recipes.insert().values(user_id=user.id, recipe_id=id)
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == id).first()
    if not db_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    db_recipe.favourites.append(current_user)
    db.commit()
    return {"message": "Recipe added to favourites"}


@router.delete("/{id}/favorite/")
def remove_from_favourite(id: int,
                          current_user: models.User = Depends(get_current_user),
                          db: SessionLocal = Depends(get_db)):
    db.execute(models.favourite_recipes.delete()
               .where((models.favourite_recipes.c.user_id == current_user.id) & (
                models.favourite_recipes.c.recipe_id == id)))
    db.commit()
    return {"message": "Recipe removed from favourites"}


@router.post("/{id}/shopping_cart/", response_model=schrec.RecipeShortDataResponse, status_code=status.HTTP_201_CREATED)
def add_to_shopping_cart(id: int,
                         db: SessionLocal = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == id).first()
    if not db_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    exists = db.execute(select(models.shopping_cart)
                        .where((models.shopping_cart.c.user_id == current_user.id) & (
                models.shopping_cart.c.recipe_id == id))
                        ).fetchone()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already have recipe with ID={id} in shopping cart"
        )
    db_cart = models.shopping_cart.insert().values(user_id=current_user.id, recipe_id=id)
    db.execute(db_cart)
    db.commit()
    return schrec.RecipeShortDataResponse(
        id=db_recipe.id,
        name=db_recipe.name,
        image=encode_image(db_recipe.image),
        cooking_time=db_recipe.cooking_time
    )


@router.delete("/{id}/shopping_cart/", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_shopping_cart(id: int,
                              db: SessionLocal = Depends(get_db),
                              current_user: models.User = Depends(get_current_user)):
    exists = db.execute(select(models.shopping_cart)
                        .where(
        (models.shopping_cart.c.user_id == current_user.id) & (models.shopping_cart.c.recipe_id == id))
                        ).fetchone()
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Haven't recipe with ID={id} in shopping cart"
        )
    db_cart = (models.shopping_cart.delete()
               .where((models.shopping_cart.c.user_id == current_user.id) & (models.shopping_cart.c.recipe_id == id)))
    db.execute(db_cart)
    db.commit()
    return
