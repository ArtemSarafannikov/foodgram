from fastapi import APIRouter, Depends, status, HTTPException, Request, Response, Query
from typing import List, Optional
from app.utils.errors import Error
from app.core.security import get_current_user
import app.schemas.recipes as schrec
import app.db.models as models
import app.services.recipes as service

router = APIRouter()

@router.get("/download_shopping_cart/")
def download_shopping_cart(current_user: models.User = Depends(get_current_user)):
    output = service.get_download_shopping_cart(current_user.id)
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
        current_user: models.User = Depends(get_current_user)
):
    return service.get_recipes(page, limit, is_favorited, is_in_shopping_cart, author, tags, request.url, current_user)


@router.get("/{id}/", response_model=schrec.RecipeResponse)
def get_recipe(id: int, current_user: models.User = Depends(get_current_user)):
    try:
        response = service.get_recipe(id, current_user)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
    return response


@router.post("/")
def create_recipe(recipe_data: schrec.RecipeCreate,
                  current_user: models.User = Depends(get_current_user)):
    try:
        response = service.create_recipe(recipe_data, current_user.id)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
    return response


@router.patch("/{id}/")
def update_recipe(id: int,
                  recipe: schrec.RecipeUpdate,
                  current_user: models.User = Depends(get_current_user)):
    try:
        response = service.update_recipe(id, recipe, current_user)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
    return response


@router.post("/{id}/favorite/")
def add_to_favourite(id: int,
                     current_user: models.User = Depends(get_current_user)):
    service.add_favourite_recipe(id, current_user)
    return {"message": "Recipe added to favourites"}


@router.delete("/{id}/favorite/")
def remove_from_favourite(id: int,
                          current_user: models.User = Depends(get_current_user)):
    service.delete_favourite_recipe(id, current_user)
    return {"message": "Recipe removed from favourites"}


@router.post("/{id}/shopping_cart/", response_model=schrec.RecipeShortDataResponse, status_code=status.HTTP_201_CREATED)
def add_to_shopping_cart(id: int,
                         current_user: models.User = Depends(get_current_user)):
    try:
        response = service.add_to_shopping_cart(id, current_user)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
    except BaseException as be:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    return response


@router.delete("/{id}/shopping_cart/", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_shopping_cart(id: int,
                              current_user: models.User = Depends(get_current_user)):
    try:
        service.remove_from_shopping_cart(id, current_user)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
    return
