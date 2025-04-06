 # Pydantic models for request/response validation
from typing import List, Optional, Dict
from pydantic import BaseModel
import datetime


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
        from_attributes = True


class DirectionBase(BaseModel):
    step_number: int
    description: str


class DirectionCreate(DirectionBase):
    pass


class Direction(DirectionBase):
    id: int
    recipe_id: int

    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True


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
        from_attributes = True


class RecipeList(BaseModel):
    recipes: List[Recipe]
    total: int


class MealPlanBase(BaseModel):
    """Base model for meal plans."""
    name: str


class MealPlanCreate(MealPlanBase):
    """Model for creating a meal plan."""
    recipe_ids: List[int] = []
    categories: List[str] = []


class MealPlanIngredient(BaseModel):
    """Model for consolidated ingredients in a meal plan."""
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None


class MealPlan(MealPlanBase):
    """Model for meal plan responses."""
    id: int
    created_at: datetime.datetime
    recipes: List[Recipe] = []
    categories: List[Category] = []
    all_ingredients: List[MealPlanIngredient] = []

    class Config:
        from_attributes = True


class MealPlanList(BaseModel):
    """Model for paginated meal plan responses."""
    meal_plans: List[MealPlan]
    total: int