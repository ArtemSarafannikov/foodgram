from fastapi import APIRouter, Depends, status, HTTPException, Request, Body
from app.utils.convert import encode_image, decode_image
from app.db.session import SessionLocal, get_db
from app.core.security import get_password_hash, get_current_user, verify_password
import app.services.users as service
import app.schemas.users as schuser
import app.schemas.recipes as schrec
import app.schemas.subscriptions as schsub
import app.db.models as models
from app.utils.errors import Error

router = APIRouter()


@router.get("/me/", response_model=schuser.UserGet)
def get_current_user_profile(current_user: models.User = Depends(get_current_user)):
    return service.get_user_response(current_user)


@router.post("/", status_code=status.HTTP_201_CREATED)
def signup(user: schuser.UserCreate):
    try:
        response = service.register_user(user)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message,
        )
    return response

@router.post("/set_password/")
def change_password(password_data: schuser.ChangePassword,
                    current_user: models.User = Depends(get_current_user)):
    try:
        service.change_password(password_data, current_user)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
    return {"detail": "Password updated successfully"}


@router.post("/reset_password/")
def reset_password(res_pas: schuser.ResetPassword):
    try:
        new_password = service.reset_password(res_pas)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
    return {"message": f"Password for {res_pas.email} was changed reseted",
            "new_password": new_password}


@router.put("/me/avatar/")
def update_avatar(avatar_data: schuser.AvatarUpload,
                  current_user: models.User = Depends(get_current_user)):
    try:
        service.update_avatar(avatar_data, current_user)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=400,
            detail="Invalid string"
        )
    return {"message": "Avatar uploaded successfully"}


@router.delete("/me/avatar/")
def delete_avatar(current_user: models.User = Depends(get_current_user)):
    av = schuser.AvatarUpload(avatar="")
    service.update_avatar(av, current_user)
    return {"message": "Avatar deleted succesfully"}


@router.get("/subscriptions/", response_model=schsub.SubscribePaginationResponse)
def get_subscriptions(page: int = 1,
                      limit: int = 6,
                      recipes_limit: int = 5,
                      request: Request = None,
                      current_user: models.User = Depends(get_current_user)):
    return service.get_subscription(page, limit, recipes_limit, request, current_user)


@router.get("/{id}/", response_model=schuser.UserResponse)
def get_user(id: int,
             current_user: models.User = Depends(get_current_user)):
    try:
        response = service.get_user(id, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e
        )
    return response


@router.get("/")
def get_users(page: int = 1,
              limit: int = 6,
              request: Request = None):
    return service.get_users(page, limit, request)


@router.post("/{id}/subscribe/", response_model=schsub.SubscribeResponse, status_code=status.HTTP_201_CREATED)
def add_subscribe(id: int,
                  recipes_limit: int = Body(default=6, embed=True),
                  current_user: models.User = Depends(get_current_user)):
    try:
        response = service.add_subscribe(id, recipes_limit, current_user)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
    return response


@router.delete("/{id}/subscribe/", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe(id: int,
                current_user: models.User = Depends(get_current_user),
                db: SessionLocal = Depends(get_db)):
    try:
        service.unsubscribe(id, current_user)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
