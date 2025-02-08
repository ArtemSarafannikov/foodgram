from pydantic import BaseModel


class Tag(BaseModel):
    id: int
    name: str
    color: str
    slug: str