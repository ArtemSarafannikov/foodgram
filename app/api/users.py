from fastapi import APIRouter, Depends, status, HTTPException, Request, Body
from app.utils.convert import encode_image, decode_image
from app.db.session import SessionLocal, get_db
from app.core.security import get_password_hash, get_current_user, verify_password
from app.utils.gen import generate_password
import app.schemas.users as schuser
import app.schemas.recipes as schrec
import app.schemas.subscriptions as schsub
import app.db.models as models

router = APIRouter()


def get_user_response(user, current_user=None):
    return schuser.UserResponse(
        email=user.email,
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_subscribed=any(subscription.id == user.id for subscription in current_user.subscriptions) if current_user else False,
        avatar=encode_image(user.avatar)
    )


def get_subscription_response(author, recipes_limit):
    author_recipes = author.recipes
    recipes = []
    recipes_count = 0

    min_len = min(recipes_limit, len(author_recipes))
    for i in range(min_len):
        recipe = author_recipes[i]
        recipes_count += 1
        recipes.append(schrec.RecipeShortDataResponse(
            id=recipe.id,
            name=recipe.name,
            image=encode_image(recipe.image),
            cooking_time=recipe.cooking_time
        ))

    return schsub.SubscribeResponse(
        email=author.email,
        id=author.id,
        username=author.username,
        first_name=author.first_name,
        last_name=author.last_name,
        avatar=encode_image(author.avatar),
        is_subscribed=True,
        recipes=recipes,
        recipes_count=recipes_count,
    )


@router.get("/me/", response_model=schuser.UserGet)
def get_current_user_profile(current_user: models.User = Depends(get_current_user)):
    return get_user_response(current_user)


@router.post("/", status_code=status.HTTP_201_CREATED)
def signup(user: schuser.UserCreate, db: SessionLocal = Depends(get_db)):
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


@router.post("/set_password/")
def change_password(password_data: schuser.ChangePassword,
                    current_user: models.User = Depends(get_current_user),
                    db: SessionLocal = Depends(get_db)):
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is wrong"
        )

    hashed_password = get_password_hash(password_data.new_password)
    current_user.hashed_password = hashed_password
    db.commit()
    return {"detail": "Password updated successfully"}


@router.post("/reset_password/")
def reset_password(res_pas: schuser.ResetPassword, db: SessionLocal = Depends(get_db)):
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


@router.put("/me/avatar/")
def update_avatar(avatar_data: schuser.AvatarUpload,
                  current_user: models.User = Depends(get_current_user),
                  db: SessionLocal = Depends(get_db)):
    try:
        decoded_file = decode_image(avatar_data.avatar)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid string"
        )
    current_user.avatar = decoded_file
    db.commit()
    return {"message": "Avatar uploaded successfully"}


@router.delete("/me/avatar/")
def delete_avatar(current_user: models.User = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    current_user.avatar = None
    db.commit()
    return {"message": "Avatar deleted succesfully"}


@router.get("/subscriptions/", response_model=schsub.SubscribePaginationResponse)
def get_subscriptions(page: int = 1,
                      limit: int = 6,
                      recipes_limit: int = 5,
                      request: Request = None,
                      current_user: models.User = Depends(get_current_user)):
    subs = current_user.subscriptions
    results = []
    total = 0
    for sub in subs:
        total += 1
        results.append(get_subscription_response(sub, recipes_limit))

    base_url = str(request.url).split("?")[0]
    next_url = (
        f"{base_url}?page={page + 1}&limit={limit}&recipes_limit={recipes_limit}"
        if (page * limit) < total else None
    )
    previous_url = (
        f"{base_url}?page={page - 1}&limit={limit}&recipes_limit={recipes_limit}"
        if page > 1 else None
    )
    return schuser.UserPaginationResponse(
        count=total,
        next=next_url,
        previous=previous_url,
        results=results
    )


@router.get("/{id}/", response_model=schuser.UserResponse)
def get_user(id: int,
             current_user: models.User = Depends(get_current_user),
             db: SessionLocal = Depends(get_db)):
    req_user = db.query(models.User).filter(models.User.id == id).first()
    if not req_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return get_user_response(req_user, current_user)


@router.get("/")
def get_users(page: int = 1,
              limit: int = 6,
              request: Request = None,
              db: SessionLocal = Depends(get_db)):
    total = db.query(models.User).count()
    users = db.query(models.User).offset((page - 1) * limit).limit(limit).all()
    results = []
    for user in users:
        results.append(get_user_response(user))

    base_url = str(request.url).split("?")[0]
    next_url = (
        f"{base_url}?page={page + 1}&limit={limit}"
        if (page * limit) < total else None
    )
    previous_url = (
        f"{base_url}?page={page - 1}&limit={limit}"
        if page > 1 else None
    )
    return schuser.UserPaginationResponse(
        count=total,
        next=next_url,
        previous=previous_url,
        results=results
    )


@router.post("/{id}/subscribe/", response_model=schsub.SubscribeResponse, status_code=status.HTTP_201_CREATED)
def add_subscribe(id: int,
                  recipes_limit: int = Body(default=6, embed=True),
                  current_user: models.User = Depends(get_current_user),
                  db: SessionLocal = Depends(get_db)):
    author = db.query(models.User).filter(models.User.id == id).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found"
        )
    if id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can't subscribe yourself"
        )
    if author in current_user.subscriptions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already have subscription to this user"
        )

    current_user.subscriptions.append(author)
    db.commit()
    return get_subscription_response(author, recipes_limit)


@router.delete("/{id}/subscribe/", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe(id: int,
                current_user: models.User = Depends(get_current_user),
                db: SessionLocal = Depends(get_db)):
    author = db.query(models.User).filter(models.User.id == id).first()
    if not author or author not in current_user.subscriptions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Haven't subscription for this user"
        )
    db.execute(models.user_subscriptions.delete().
               where((models.user_subscriptions.c.user_id == current_user.id) &
                     (models.user_subscriptions.c.author_id == id)))
    db.commit()
    return
