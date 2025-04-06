from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Define request and response models


class IngredientModel(BaseModel):
    """Response model for ingredient."""
    id: int
    quantity: Optional[str] = None
    unit: Optional[str] = None
    name: str
    is_header: int = 0

    model_config = {"extra": "allow"}


class DirectionModel(BaseModel):
    """Response model for direction."""
    id: int
    step_number: int
    description: str

    model_config = {"extra": "allow"}


class CategoryModel(BaseModel):
    """Response model for category."""
    id: int
    name: str

    model_config = {"extra": "allow"}


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

    model_config = {"extra": "allow"}


class MealPlanIngredientModel(BaseModel):
    """Model for consolidated ingredients in a meal plan."""
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None

    model_config = {"extra": "allow"}


class MealPlanModel(BaseModel):
    """Response model for meal plan."""
    id: int
    name: str
    created_at: datetime
    recipes: List[RecipeModel] = []
    all_ingredients: List[MealPlanIngredientModel] = []

    model_config = {"extra": "allow"}


class MealPlanCreateRequest(BaseModel):
    """
    Request model for creating a new meal plan.
    
    A meal plan must have a name and can optionally include recipes at creation time.
    """
    name: str = Field(
        description="The name of the meal plan. Required when creating a new plan."
    )
    recipe_ids: List[int] = Field(
        default=[], 
        description="List of recipe IDs to include in the meal plan. Can be empty for a plan with no recipes."
    )
    categories: List[str] = Field(
        default=[],
        description="List of category names to associate with the meal plan."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Weekly Dinner Plan",
                    "recipe_ids": [1, 2, 3],
                    "categories": ["Dinner", "Weekly"]
                }
            ]
        }
    }


class MealPlanUpdateRequest(BaseModel):
    """
    Request model for updating an existing meal plan.
    
    Specify only the fields you want to update. Fields set to None will be ignored.
    Use update_categories_only=True to update only the categories while preserving other fields.
    """
    name: Optional[str] = Field(
        default=None, 
        description="The new name for the meal plan. Leave as null/None to keep the existing name."
    )
    recipe_ids: Optional[List[int]] = Field(
        default=None, 
        description="A list of recipe IDs to include in the meal plan. Replaces the existing list if provided. Set to an empty list to remove all recipes."
    )
    categories: Optional[List[str]] = Field(
        default=None, 
        description="A list of category names to associate with the meal plan. Replaces the existing list if provided. Set to an empty list to remove all categories."
    )
    update_categories_only: bool = Field(
        default=False, 
        description="Set to true if ONLY the categories should be updated, ignoring other fields like name and recipe_ids."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Updated Weekly Meals",
                    "recipe_ids": [5, 8, 12],
                    "categories": ["Dinner", "Quick Meals"],
                    "update_categories_only": False
                },
                {
                    "categories": ["Holiday", "Special Occasion"],
                    "update_categories_only": True
                }
            ]
        }
    }


class IngredientCreateModel(BaseModel):
    """
    Request model for ingredient creation.
    
    An ingredient must have a name and can optionally include quantity and unit information.
    Set is_header=1 for section headers in ingredient lists (e.g., "For the sauce:").
    """
    quantity: Optional[str] = Field(
        default=None,
        description="The quantity of the ingredient (e.g., '2', '1/2', 'a pinch'). Leave as null/None for ingredients without quantities."
    )
    unit: Optional[str] = Field(
        default=None,
        description="The unit of measurement (e.g., 'cups', 'tbsp', 'g'). Leave as null/None for ingredients without units."
    )
    name: str = Field(
        description="The name of the ingredient. Required."
    )
    is_header: int = Field(
        default=0,
        description="Set to 1 if this is a section header in the ingredients list (e.g., 'For the sauce:'). Default is 0."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "quantity": "2",
                    "unit": "cups",
                    "name": "all-purpose flour",
                    "is_header": 0
                },
                {
                    "name": "For the sauce:",
                    "is_header": 1
                }
            ]
        }
    }


class DirectionCreateModel(BaseModel):
    """
    Request model for recipe direction/step creation.
    
    Each direction requires a step number and description text.
    """
    step_number: int = Field(
        description="The order number of this step in the recipe instructions."
    )
    description: str = Field(
        description="The text description of this step in the recipe."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "step_number": 1,
                    "description": "Preheat oven to 350°F (175°C)."
                }
            ]
        }
    }


class RecipeCreateRequest(BaseModel):
    """
    Request model for creating a new recipe.
    
    A recipe must have a name and can include various optional fields like source, rating,
    preparation time, cooking time, categories, ingredients, and directions.
    """
    name: str = Field(
        description="The name of the recipe. Required when creating a new recipe."
    )
    source: Optional[str] = Field(
        default=None, 
        description="The source of the recipe (e.g., website, cookbook, person). Optional."
    )
    rating: int = Field(
        default=0, 
        description="Rating of the recipe on a scale from 0 to 5. Default is 0 (unrated)."
    )
    prep_time: Optional[str] = Field(
        default=None, 
        description="Preparation time as a string (e.g., '10 minutes', '1 hour'). Optional."
    )
    cook_time: Optional[str] = Field(
        default=None, 
        description="Cooking time as a string (e.g., '30 minutes', '2 hours'). Optional."
    )
    categories: List[str] = Field(
        default=[], 
        description="List of category names for the recipe. Categories will be created if they don't exist."
    )
    ingredients: List[IngredientCreateModel] = Field(
        default=[], 
        description="List of ingredients for the recipe. Each ingredient must include at least a name."
    )
    directions: List[DirectionCreateModel] = Field(
        default=[], 
        description="List of directions for the recipe. Each direction must include a step number and description."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Chocolate Chip Cookies",
                    "source": "Grandma's Recipe Book",
                    "rating": 5,
                    "prep_time": "15 minutes",
                    "cook_time": "12 minutes",
                    "categories": ["Dessert", "Baking"],
                    "ingredients": [
                        {"name": "For the dough:", "is_header": 1},
                        {"quantity": "2 1/4", "unit": "cups", "name": "all-purpose flour"},
                        {"quantity": "1", "unit": "tsp", "name": "baking soda"}
                    ],
                    "directions": [
                        {"step_number": 1, "description": "Preheat oven to 375°F."},
                        {"step_number": 2, "description": "Mix dry ingredients in a bowl."}
                    ]
                }
            ]
        }
    }


class RecipeUpdateRequest(BaseModel):
    """
    Request model for updating an existing recipe.
    
    Specify only the fields you want to update. Fields set to None will be ignored.
    Use update_categories_only=True to update only the categories while preserving other fields.
    """
    name: Optional[str] = Field(
        default=None, 
        description="The new name for the recipe. Leave as null/None to keep the existing name."
    )
    source: Optional[str] = Field(
        default=None, 
        description="The source of the recipe. Leave as null/None to keep the existing source."
    )
    rating: Optional[int] = Field(
        default=None, 
        description="Rating of the recipe on a scale from 0 to 5. Leave as null/None to keep the existing rating."
    )
    prep_time: Optional[str] = Field(
        default=None, 
        description="Preparation time as a string. Leave as null/None to keep the existing prep time."
    )
    cook_time: Optional[str] = Field(
        default=None, 
        description="Cooking time as a string. Leave as null/None to keep the existing cook time."
    )
    categories: Optional[List[str]] = Field(
        default=None, 
        description="List of category names for the recipe. Replaces the existing list if provided. Set to an empty list to remove all categories."
    )
    ingredients: Optional[List[IngredientCreateModel]] = Field(
        default=None, 
        description="List of ingredients for the recipe. Replaces the existing list if provided. Set to an empty list to remove all ingredients."
    )
    directions: Optional[List[DirectionCreateModel]] = Field(
        default=None, 
        description="List of directions for the recipe. Replaces the existing list if provided. Set to an empty list to remove all directions."
    )
    update_categories_only: bool = Field(
        default=False, 
        description="Set to true if ONLY the categories should be updated, ignoring other fields."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Improved Chocolate Chip Cookies",
                    "rating": 5,
                    "categories": ["Dessert", "Family Favorite"],
                    "update_categories_only": False
                },
                {
                    "categories": ["Holiday", "Christmas"],
                    "update_categories_only": True
                }
            ]
        }
    }


# Models for the simplified getters
class RecipeGetRequest(BaseModel):
    """
    Request model for getting recipes with flexible column selection and filtering.
    
    This model supports various filtering options and allows selecting which columns
    to include in the response for more efficient data retrieval.
    """
    id: Optional[int] = Field(
        default=None, 
        description="Recipe ID to fetch a specific recipe. If provided, other filters are ignored."
    )
    name: Optional[str] = Field(
        default=None, 
        description="Search term for recipe name or source. Performs a case-insensitive partial match."
    )
    ingredient: Optional[str] = Field(
        default=None, 
        description="Ingredient to search for. Returns recipes containing this ingredient."
    )
    category: Optional[str] = Field(
        default=None, 
        description="Category to filter by. Returns recipes in this category."
    )
    max_total_time: Optional[int] = Field(
        default=None, 
        description="Maximum total time (prep + cook) in minutes. Returns recipes with total time less than or equal to this value."
    )
    skip: int = Field(
        default=0, 
        description="Number of recipes to skip (for pagination)."
    )
    limit: int = Field(
        default=10, 
        description="Maximum number of recipes to return (page size for pagination)."
    )
    columns: List[str] = Field(
        default=["id", "name", "rating", "prep_time", "cook_time"],
        description="List of columns to include in the response. Available columns: id, name, source, rating, prep_time, cook_time, ingredients, directions, categories."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "chicken",
                    "category": "Dinner",
                    "limit": 5,
                    "columns": ["id", "name", "rating", "ingredients"]
                },
                {
                    "id": 42,
                    "columns": ["id", "name", "ingredients", "directions", "categories"]
                }
            ]
        }
    }


class MealPlanGetRequest(BaseModel):
    """
    Request model for getting meal plans with flexible column selection and filtering.
    
    This model supports various filtering options and allows selecting which columns
    to include in the response for more efficient data retrieval.
    """
    id: Optional[int] = Field(
        default=None, 
        description="Meal plan ID to fetch a specific meal plan. If provided, other filters are ignored."
    )
    name: Optional[str] = Field(
        default=None, 
        description="Search term for meal plan name. Performs a case-insensitive partial match."
    )
    skip: int = Field(
        default=0, 
        description="Number of meal plans to skip (for pagination)."
    )
    limit: int = Field(
        default=10, 
        description="Maximum number of meal plans to return (page size for pagination)."
    )
    columns: List[str] = Field(
        default=["id", "name", "created_at"],
        description="List of columns to include in the response. Available columns: id, name, created_at, categories, recipes, all_ingredients."
    )
    include_recipes: bool = Field(
        default=False, 
        description="Whether to include full recipe details in the response. Set to true to include recipes if 'recipes' is in columns."
    )
    include_ingredients: bool = Field(
        default=False, 
        description="Whether to include consolidated ingredients in the response. Set to true to include ingredients if 'all_ingredients' is in columns."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Weekly",
                    "limit": 5,
                    "columns": ["id", "name", "created_at", "recipes"],
                    "include_recipes": True
                },
                {
                    "id": 3,
                    "columns": ["id", "name", "recipes", "all_ingredients"],
                    "include_recipes": True,
                    "include_ingredients": True
                }
            ]
        }
    }


class DynamicRecipeModel(BaseModel):
    """Dynamic response model for recipe with flexible fields."""
    model_config = {"extra": "allow"}


class DynamicMealPlanModel(BaseModel):
    """Dynamic response model for meal plan with flexible fields."""
    model_config = {"extra": "allow"}


class RecipeGetResponse(BaseModel):
    """
    Response model for recipe getter.
    
    Contains a list of recipes matching the search criteria and the total count.
    """
    recipes: List[DynamicRecipeModel] = Field(
        description="List of recipes matching the search criteria with the requested columns."
    )
    total: int = Field(
        description="Total number of recipes matching the search criteria (before pagination)."
    )


class MealPlanGetResponse(BaseModel):
    """
    Response model for meal plan getter.
    
    Contains a list of meal plans matching the search criteria and the total count.
    """
    meal_plans: List[DynamicMealPlanModel] = Field(
        description="List of meal plans matching the search criteria with the requested columns."
    )
    total: int = Field(
        description="Total number of meal plans matching the search criteria (before pagination)."
    )
