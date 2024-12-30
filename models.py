from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary, Table
from sqlalchemy.orm import declarative_base, relationship
from database import engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    avatar = Column(LargeBinary, nullable=True)

    recipes = relationship("Recipe", back_populates="author")


class Ingredient(Base):
    __tablename__ = 'ingredients'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    measurement_unit = Column(String)

    recipes = relationship("RecipeIngredient", back_populates="ingredient")


class Recipe(Base):
    __tablename__ = 'recipes'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    image = Column(LargeBinary, nullable=True)
    cooking_time = Column(Integer)
    text = Column(String)
    author_id = Column(Integer, ForeignKey('users.id'))

    author = relationship("User", back_populates="recipes")
    ingredients = relationship("RecipeIngredient", back_populates="recipe")
    tags = relationship("Tag", secondary="recipe_tags", back_populates="recipes")


class RecipeIngredient(Base):
    __tablename__ = 'recipe_ingredients'
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'))
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'))
    amount = Column(Integer)

    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipes")


class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    slug = Column(String, unique=True)

    recipes = relationship("Recipe", secondary="recipe_tags", back_populates="tags")


recipe_tags = Table(
    'recipe_tags', Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)


Base.metadata.create_all(bind=engine)
