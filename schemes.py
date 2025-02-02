from pydantic import BaseModel, EmailStr
from typing import List, Optional


class Token(BaseModel):
    auth_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str
    first_name: str
    last_name: str


class UserGet(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    avatar: str


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


class ResetPassword(BaseModel):
    email: str


class AvatarUpload(BaseModel):
    avatar: str


class Author(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    is_subscribed: bool


class Ingredient(BaseModel):
    id: int
    name: str
    measurement_unit: str
    amount: int


class Tag(BaseModel):
    id: int
    name: str
    color: str
    slug: str


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


class IngredientSchema(BaseModel):
    id: int
    amount: int


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


class UserResponse(BaseModel):
    email: str
    id: int
    username: str
    first_name: str
    last_name: str
    is_subscribed: bool
    avatar: Optional[str]


class UserPaginationResponse(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[UserResponse]


class RecipeShortDataResponse(BaseModel):
    id: int
    name: str
    image: str
    cooking_time: int


class SubscribeResponse(UserResponse):
    recipes: List[RecipeShortDataResponse]
    recipes_count: int

class SubscribePaginationResponse(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[SubscribeResponse]
