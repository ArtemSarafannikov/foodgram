from pydantic import BaseModel
from typing import List, Optional
from app.schemas.users import UserResponse
from app.schemas.recipes import RecipeShortDataResponse


class SubscribeResponse(UserResponse):
    recipes: List[RecipeShortDataResponse]
    recipes_count: int


class SubscribePaginationResponse(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[SubscribeResponse]