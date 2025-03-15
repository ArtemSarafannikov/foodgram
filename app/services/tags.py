from app.repositories import repo
from app.utils.errors import Error
from fastapi import status


def get_tags():
    return repo.get_tags()


def get_tag(id: int):
    tag = repo.get_tag(id)
    if not tag:
        raise Error(status.HTTP_404_NOT_FOUND, "Tag not found")
    return tag
