from fastapi import APIRouter, Depends, status, HTTPException
from app.db.session import SessionLocal, get_db
import app.db.models as models

router = APIRouter()


@router.get("/")
def get_tags(db: SessionLocal = Depends(get_db)):
    tags = db.query(models.Tag).all()
    return tags


@router.get("/{id}/")
def get_tag(id: int, db: SessionLocal = Depends(get_db)):
    tag = db.query(models.Tag).filter(models.Tag.id == id).first()
    if not tag:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag
