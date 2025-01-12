from fastapi import FastAPI, Depends, HTTPException, status, Body, File, UploadFile, Query, Request
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal, get_db
from utility import *
from typing import List

import base64
import models
import schemes

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/token/login/')


async def get_current_user(token: str = Depends(oauth2_scheme), db: SessionLocal = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise credentials_exception
    return user


def get_recipe_response(recipe):
    return schemes.RecipeResponse(
        id=recipe.id,
        tags=[
            schemes.Tag(
                id=tag.id,
                name=tag.name,
                color='#E26C2D',
                slug=tag.slug
            ) for tag in recipe.tags
        ],
        author=schemes.Author(
            id=recipe.author.id,
            email=recipe.author.email,
            username=recipe.author.username,
            first_name=recipe.author.first_name,
            last_name=recipe.author.last_name,
            is_subscribed=False
        ),
        ingredients=[
            schemes.Ingredient(
                id=ingredient.id,
                name=ingredient.ingredient.name,
                measurement_unit=ingredient.ingredient.measurement_unit,
                amount=ingredient.amount
            ) for ingredient in recipe.ingredients
        ],
        is_favorited=False,
        is_in_shopping_cart=False,
        name=recipe.name,
        image=encode_image(recipe.image),
        text=recipe.text,
        cooking_time=recipe.cooking_time
    )


@app.post('/api/auth/token/login/', response_model=schemes.Token)
def login(login_request: schemes.LoginRequest, db: SessionLocal = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == login_request.email).first()
    if not user or not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"auth_token": access_token, "token_type": "Bearer"}


@app.post("/api/auth/token/logout/")
def logout():
    return {"message": "successful"}


@app.get("/api/users/me/", response_model=schemes.UserGet)
def get_current_user_profile(current_user: models.User = Depends(get_current_user)):
    current_user.avatar = encode_image(current_user.avatar)
    return current_user


@app.post("/api/users/", status_code=status.HTTP_201_CREATED)
def signup(user: schemes.UserCreate, db: SessionLocal = Depends(get_db)):
    exists = (db.query(models.User).
              filter((models.User.email == user.email) | (models.User.username == user.username)).all())
    if len(exists) > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User with this email or username already exists",
        )

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/api/users/set_password/")
def change_password(password_data: schemes.ChangePassword,
                    user: models.User = Depends(get_current_user),
                    db: SessionLocal = Depends(get_db)):
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is wrong"
        )

    hashed_password = get_password_hash(password_data.new_password)
    user.hashed_password = hashed_password
    db.commit()
    return {"detail": "Password updated successfully"}


@app.post("/api/users/reset_password/")
def reset_password(res_pas: schemes.ResetPassword, db: SessionLocal = Depends(get_db)):
    ''' EXPERIMENTAL!!! DO NOT USE THIS IN PRODUCTION '''
    new_password = generate_password()
    user = db.query(models.User).filter(models.User.email == res_pas.email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User with this email not found"
        )
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"message": f"Password for {res_pas.email} was changed reseted",
            "new_password": new_password}


@app.put("/api/users/me/avatar/")
def update_avatar(avatar_data: schemes.AvatarUpload,
                  user: models.User = Depends(get_current_user),
                  db: SessionLocal = Depends(get_db)):
    try:
        decoded_file = decode_image(avatar_data.avatar)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid string"
        )
    user.avatar = decoded_file
    db.commit()
    return {"message": "Avatar uploaded successfully"}


@app.delete("/api/users/me/avatar/")
def delete_avatar(user: models.User = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    user.avatar = None
    db.commit()
    return {"message": "Avatar deleted succesfully"}


@app.get("/api/recipes/", response_model=schemes.RecipePaginationResponse)
def get_recipes(
        page: int = 1,
        limit: int = 6,
        is_favorited: int = 0,
        is_in_shopping_cart: int = 0,
        author: Optional[int] = None,
        tags: Optional[List[int]] = Query(None),
        request: Request = None,
        db: SessionLocal = Depends(get_db)
):
    query = db.query(models.Recipe)
    if author:
        query = query.filter(models.Recipe.author_id == author)
    if tags:
        query = query.filter(models.Recipe.tags.any(models.Tag.id.in_(tags)))

    total = query.count()
    recipes = query.offset((page - 1) * limit).limit(limit).all()

    results = []
    for recipe in recipes:
        results.append(get_recipe_response(recipe))

    base_url = str(request.url).split("?")[0]
    next_url = (
        f"{base_url}?page={page + 1}&limit={limit}"
        if (page * limit) < total else None
    )
    previous_url = (
        f"{base_url}?page={page - 1}&limit={limit}"
        if page > 1 else None
    )
    return schemes.RecipePaginationResponse(
        count=total,
        next=next_url,
        previous=previous_url,
        results=results
    )


@app.get("/api/recipes/{id}/", response_model=schemes.RecipeResponse)
def get_recipe(id: int, db: SessionLocal = Depends(get_db)):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == id).first()
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail="No recipe with this id"
        )
    return get_recipe_response(recipe)


@app.get("/api/tags/")
def get_tags():
    return []
