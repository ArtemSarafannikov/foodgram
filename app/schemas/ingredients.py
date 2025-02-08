from pydantic import BaseModel


class Ingredient(BaseModel):
    id: int
    name: str
    measurement_unit: str
    amount: int


class IngredientSchema(BaseModel):
    id: int
    amount: int
