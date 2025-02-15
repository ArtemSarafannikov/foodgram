from fastapi import APIRouter, HTTPException
from app.utils.errors import Error
import app.services.tags as service

router = APIRouter()


@router.get("/")
def get_tags():
    tags = service.get_tags()
    return tags


@router.get("/{id}/")
def get_tag(id: int):
    try:
        tag = service.get_tag(id)
    except Error as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message,
        )
    return tag
