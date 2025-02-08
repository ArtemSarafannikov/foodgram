from pydantic import BaseModel
from typing import List, Optional
from app.schemas.ingredients import Ingredient, IngredientSchema
from app.schemas.tags import Tag
from app.schemas.users import Author


class RecipeResponse(BaseModel):
    id: int
    tags: List[Tag]
    author: Author
    ingredients: List[Ingredient]
    is_favorited: bool
    is_in_shopping_cart: bool
    name: str
    image: Optional[str]
    text: str
    cooking_time: int


class RecipeCreate(BaseModel):
    ingredients: List[IngredientSchema]
    tags: List[int]
    image: Optional[str] = None
    name: str
    text: str
    cooking_time: int


class RecipeUpdate(RecipeCreate):
    id: int


class RecipePaginationResponse(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[RecipeResponse]


class RecipeShortDataResponse(BaseModel):
    id: int
    name: str
    image: str
    cooking_time: int
