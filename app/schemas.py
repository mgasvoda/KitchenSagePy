 # Pydantic models for request/response validation
from typing import List, Optional
from pydantic import BaseModel


class IngredientBase(BaseModel):
    quantity: Optional[str] = None
    unit: Optional[str] = None
    name: str
    is_header: int = 0


class IngredientCreate(IngredientBase):
    pass


class Ingredient(IngredientBase):
    id: int
    recipe_id: int

    class Config:
        orm_mode = True


class DirectionBase(BaseModel):
    step_number: int
    description: str


class DirectionCreate(DirectionBase):
    pass


class Direction(DirectionBase):
    id: int
    recipe_id: int

    class Config:
        orm_mode = True


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int

    class Config:
        orm_mode = True


class RecipeBase(BaseModel):
    name: str
    source: Optional[str] = None
    rating: int = 0
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None


class RecipeCreate(RecipeBase):
    categories: List[str] = []
    ingredients: List[IngredientCreate] = []
    directions: List[DirectionCreate] = []


class Recipe(RecipeBase):
    id: int
    ingredients: List[Ingredient] = []
    directions: List[Direction] = []
    categories: List[Category] = []

    class Config:
        orm_mode = True


class RecipeList(BaseModel):
    recipes: List[Recipe]
    total: int