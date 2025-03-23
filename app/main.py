from fastapi import FastAPI
from app.api import auth, ingredients, recipes, tags, users

API = FastAPI(title="Foodgram API")

API.include_router(auth.router, prefix="/api/auth")
API.include_router(ingredients.router, prefix="/api/ingredients")
API.include_router(recipes.router, prefix="/api/recipes")
API.include_router(tags.router, prefix="/api/tags")
API.include_router(users.router, prefix="/api/users")

@API.get("/test")
def test():
    return {"test": "test"}