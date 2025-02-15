from fastapi import APIRouter, HTTPException
from app.utils.errors import Error
import app.services.ingredients as service

router = APIRouter()


@router.get("/")
def get_ingredients(name: str):
    ingredients = service.get_ingredients(name)
    return ingredients


@router.get("/{id}/")
def get_ingredient(id: int):
    try:
        ingredient = service.get_ingredient(id)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message,
        )
    return ingredient
