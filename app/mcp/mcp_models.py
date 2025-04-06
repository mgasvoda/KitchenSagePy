from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Define request and response models


class IngredientModel(BaseModel):
    """Response model for ingredient."""
    id: int
    quantity: Optional[str] = None
    unit: Optional[str] = None
    name: str
    is_header: int = 0

    class Config:
        from_attributes = True


class DirectionModel(BaseModel):
    """Response model for direction."""
    id: int
    step_number: int
    description: str

    class Config:
        from_attributes = True


class CategoryModel(BaseModel):
    """Response model for category."""
    id: int
    name: str

    class Config:
        from_attributes = True


class RecipeModel(BaseModel):
    """Response model for recipe."""
    id: int
    name: str
    source: Optional[str] = None
    rating: int = 0
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    ingredients: List[IngredientModel] = []
    directions: List[DirectionModel] = []
    categories: List[CategoryModel] = []

    class Config:
        from_attributes = True


class MealPlanIngredientModel(BaseModel):
    """Model for consolidated ingredients in a meal plan."""
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None


class MealPlanModel(BaseModel):
    """Response model for meal plan."""
    id: int
    name: str
    created_at: datetime
    recipes: List[RecipeModel] = []
    all_ingredients: List[MealPlanIngredientModel] = []

    class Config:
        from_attributes = True


class MealPlanCreateRequest(BaseModel):
    """Request model for creating a meal plan."""
    name: str
    recipe_ids: List[int] = Field([], description="List of recipe IDs to include in the meal plan")


class MealPlanUpdateRequest(BaseModel):
    """Request model for updating a meal plan."""
    name: str
    recipe_ids: List[int] = Field([], description="List of recipe IDs to include in the meal plan")


class RecipeCategoryUpdateRequest(BaseModel):
    """Request model for updating recipe categories."""
    categories: List[str] = Field([], description="List of category names to assign to the recipe")


class MealPlanCategoryUpdateRequest(BaseModel):
    """Request model for updating meal plan categories."""
    categories: List[str] = Field([], description="List of category names to assign to the meal plan")


class IngredientCreateModel(BaseModel):
    """Request model for ingredient creation."""
    quantity: Optional[str] = None
    unit: Optional[str] = None
    name: str
    is_header: int = 0


class DirectionCreateModel(BaseModel):
    """Request model for direction creation."""
    step_number: int
    description: str


class RecipeCreateRequest(BaseModel):
    """Request model for recipe creation."""
    name: str
    source: Optional[str] = Field(None, description="Source of the recipe")
    rating: int = Field(0, description="Rating of the recipe (0-5)")
    prep_time: Optional[str] = Field(None, description="Preparation time (e.g., '10 minutes')")
    cook_time: Optional[str] = Field(None, description="Cooking time (e.g., '30 minutes')")
    categories: List[str] = Field([], description="List of category names for the recipe")
    ingredients: List[IngredientCreateModel] = Field([], description="List of ingredients for the recipe")
    directions: List[DirectionCreateModel] = Field([], description="List of directions for the recipe")


# Models for the simplified getters
class RecipeGetRequest(BaseModel):
    """Request model for getting recipes with flexible column selection."""
    id: Optional[int] = Field(None, description="Recipe ID to fetch a specific recipe")
    name: Optional[str] = Field(None, description="Search term for recipe name or source")
    ingredient: Optional[str] = Field(None, description="Ingredient to search for")
    category: Optional[str] = Field(None, description="Category to filter by")
    max_total_time: Optional[int] = Field(None, description="Maximum total time (prep + cook) in minutes")
    skip: int = Field(0, description="Number of recipes to skip (for pagination)")
    limit: int = Field(10, description="Maximum number of recipes to return")
    columns: List[str] = Field(
        default=["id", "name", "rating", "prep_time", "cook_time"],
        description="List of columns to include in the response"
    )


class MealPlanGetRequest(BaseModel):
    """Request model for getting meal plans with flexible column selection."""
    id: Optional[int] = Field(None, description="Meal plan ID to fetch a specific meal plan")
    name: Optional[str] = Field(None, description="Search term for meal plan name")
    skip: int = Field(0, description="Number of meal plans to skip (for pagination)")
    limit: int = Field(10, description="Maximum number of meal plans to return")
    columns: List[str] = Field(
        default=["id", "name", "created_at"],
        description="List of columns to include in the response"
    )
    include_recipes: bool = Field(False, description="Whether to include recipes in the response")
    include_ingredients: bool = Field(False, description="Whether to include consolidated ingredients in the response")


class DynamicRecipeModel(BaseModel):
    """Dynamic response model for recipe with flexible fields."""
    model_config = {"extra": "allow"}


class DynamicMealPlanModel(BaseModel):
    """Dynamic response model for meal plan with flexible fields."""
    model_config = {"extra": "allow"}


class RecipeGetResponse(BaseModel):
    """Response model for recipe getter."""
    recipes: List[DynamicRecipeModel]
    total: int


class MealPlanGetResponse(BaseModel):
    """Response model for meal plan getter."""
    meal_plans: List[DynamicMealPlanModel]
    total: int
