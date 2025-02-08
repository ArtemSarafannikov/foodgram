from fastapi import APIRouter, Depends, status, HTTPException
from app.db.session import SessionLocal, get_db
import app.db.models as models

router = APIRouter()


@router.get("/")
def get_ingredients(name: str, db: SessionLocal = Depends(get_db)):
    ingredients = db.query(models.Ingredient).filter(models.Ingredient.name.like(f"%{name}%")).all()
    return ingredients


@router.get("/{id}/")
def get_ingredients(id: int, db: SessionLocal = Depends(get_db)):
    ingredient = db.query(models.Ingredient).filter(models.Ingredient.id == id).first()
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found"
        )
    return ingredient
