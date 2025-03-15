from app.utils.convert import encode_image, decode_image
from fastapi import status, Request
from app.core.security import get_password_hash, verify_password
from app.utils.gen import generate_password
from app.utils.errors import Error
import app.schemas.users as schuser
import app.schemas.recipes as schrec
import app.schemas.subscriptions as schsub
import app.db.models as models
from app.repositories import repo


def get_user_response(user: models.User, current_user: models.User=None) -> schuser.UserResponse:
    return schuser.UserResponse(
        email=user.email,
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_subscribed=any(subscription.id == user.id for subscription in current_user.subscriptions) if current_user else False,
        avatar=encode_image(user.avatar)
    )


def get_subscription_response(author: models.User, recipes_limit: int) -> schsub.SubscribeResponse:
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


def register_user(user: schuser.UserCreate) -> models.User:
    exists = repo.get_users_by_email_username(user.email, user.username)
    if len(exists) > 0:
        raise Error(status.HTTP_401_UNAUTHORIZED, "User with this email or username already exists")
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password
    )
    return repo.save_user(db_user)


def change_password(password_data: schuser.ChangePassword,
                    user: models.User) -> None:
    if not verify_password(password_data.current_password, user.hashed_password):
        raise Error(status.HTTP_401_UNAUTHORIZED, "Current password is wrong")
    hashed_password = get_password_hash(password_data.new_password)
    changed_user = user
    changed_user.hashed_password = hashed_password
    repo.update_user(user, changed_user)


def reset_password(res_pas: schuser.ResetPassword) -> str:
    ''' EXPERIMENTAL!!! DO NOT USE THIS IN PRODUCTION '''
    new_password = generate_password()
    user = repo.get_users_by_email_username(res_pas.email, "")
    if len(user) == 0:
        raise Error(status.HTTP_404_NOT_FOUND, "User with this email not found")
    user = user[0]
    hashed_password = get_password_hash(new_password)
    changed_user = user
    changed_user.hashed_password = hashed_password
    repo.update_user(user, changed_user)
    return new_password


def update_avatar(avatar_data: schuser.AvatarUpload,
                  user: models.User) -> None:
    changed_user = user
    if avatar_data.avatar != "":
        decoded_file = decode_image(avatar_data.avatar)
        changed_user.avatar = decoded_file
    else:
        changed_user.avatar = None
    repo.update_user(user, changed_user)


def get_subscription(page: int,
                     limit: int,
                     recipes_limit: int,
                     request: Request,
                     user: models.User) -> schuser.UserPaginationResponse:
    subs = user.subscriptions
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


def get_user(id: int,
             user: models.User) -> schsub.UserResponse:
    req_user = repo.get_user_by_id(id)
    if not req_user:
        raise Error(status.HTTP_404_NOT_FOUND, "User not found")
    return get_user_response(req_user, user)


def get_users(page: int,
              limit: int,
              request: Request) -> schuser.UserPaginationResponse:
    total = repo.get_count_users()
    offset = (page - 1) * limit
    users = repo.get_users_pagination(limit, offset)
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


def add_subscribe(id: int,
                  recipes_limit: int,
                  user: models.User) -> schsub.SubscribeResponse:
    author = repo.get_user_by_id(id)
    if not author:
        raise Error(status.HTTP_404_NOT_FOUND, "Author not found")
    if id == user.id:
        raise Error(status.HTTP_400_BAD_REQUEST, "Can't subscribe yourself")
    if author in user.subscriptions:
        raise Error(status.HTTP_400_BAD_REQUEST, "Already have subscription to this user")

    repo.add_subscription(user, author)
    return get_subscription_response(author, recipes_limit)


def unsubscribe(id: int,
                user: models.User) -> None:
    author = repo.get_user_by_id(id)
    if not author or author not in user.subscriptions:
        raise Error(status.HTTP_400_BAD_REQUEST, "Haven't subscription for this user")
    repo.delete_subscribe(user, author)
