"""
MCP server implementation for KitchenSagePy recipe search functionality.
Allows searching recipes by name, ingredient, and total time.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

import sys
import os
import traceback

# Handle imports for both direct execution and module import
try:
    # Try relative imports first (when imported as a module)
    from .. import models, crud, schemas
    from ..database import SessionLocal, engine
except ImportError:
    # Fall back to absolute imports (when run directly)
    # Add the project root to sys.path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from app import models, crud, schemas
    from app.database import SessionLocal, engine


# Create a named server
mcp = FastMCP("KitchenSagePy")

def debug_print_exception(e: Exception):
    print("Exception during startup:", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)


# Define request and response models
class RecipeSearchRequest(BaseModel):
    """Request model for recipe search."""
    name: Optional[str] = Field(None, description="Search term for recipe name")
    ingredient: Optional[str] = Field(None, description="Ingredient to search for")
    category: Optional[str] = Field(None, description="Category to filter by")
    max_total_time: Optional[int] = Field(None, description="Maximum total time (prep + cook) in minutes")
    skip: int = Field(0, description="Number of recipes to skip (for pagination)")
    limit: int = Field(100, description="Maximum number of recipes to return")


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


class SimpleRecipeModel(BaseModel):
    """Simplified response model for recipe with only essential fields."""
    id: int
    name: str
    rating: int = 0
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None

    class Config:
        from_attributes = True


class RecipeSearchResponse(BaseModel):
    """Response model for recipe search."""
    recipes: List[SimpleRecipeModel]
    total: int


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


class MealPlanListResponse(BaseModel):
    """Response model for meal plan list."""
    meal_plans: List[MealPlanModel]
    total: int


@mcp.tool()
def search_recipes(
    ctx: Context, 
    name: Optional[str] = None,
    ingredient: Optional[str] = None,
    category: Optional[str] = None,
    max_total_time: Optional[int] = None,
    skip: int = 0,
    limit: int = 10
) -> RecipeSearchResponse:
    """
    Search for recipes with optional filtering by name, ingredient, and total time.
    
    Args:
        ctx: MCP context
        name: Search term for recipe name or source
        ingredient: Ingredient to search for
        category: Category to filter by
        max_total_time: Maximum total time (prep + cook) in minutes
        skip: Number of recipes to skip (for pagination)
        limit: Maximum number of recipes to return
        
    Returns:
        List of recipes matching the criteria and total count
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Call the existing CRUD function to search for recipes
        recipes = crud.get_recipes(
            db=db,
            skip=skip,
            limit=limit,
            search=name,
            category=category,
            ingredient=ingredient,
            max_total_time=max_total_time
        )
        
        # Get the total count
        total = crud.count_recipes(
            db=db,
            search=name,
            category=category,
            ingredient=ingredient,
            max_total_time=max_total_time
        )
        
        # Convert to simplified recipe models
        simple_recipes = [
            SimpleRecipeModel(
                id=recipe.id,
                name=recipe.name,
                rating=recipe.rating,
                prep_time=recipe.prep_time,
                cook_time=recipe.cook_time
            ) for recipe in recipes
        ]
        
        # Return the response
        return RecipeSearchResponse(recipes=simple_recipes, total=total)
    finally:
        db.close()


@mcp.tool()
def get_recipe_by_id(ctx: Context, recipe_id: int) -> Optional[RecipeModel]:
    """
    Get a specific recipe by ID.
    
    Args:
        ctx: MCP context
        recipe_id: ID of the recipe to retrieve
        
    Returns:
        Recipe details or None if not found
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Call the existing CRUD function to get the recipe
        recipe = crud.get_recipe(db, recipe_id=recipe_id)
        
        if recipe is None:
            return None
        
        return RecipeModel.model_validate(recipe)
    finally:
        db.close()


@mcp.tool()
def get_categories(ctx: Context) -> List[CategoryModel]:
    """
    Get all recipe categories.
    
    Args:
        ctx: MCP context
        
    Returns:
        List of all categories
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Query all categories
        categories = db.query(models.Category).order_by(models.Category.name).all()
        
        # Convert to response model
        return [CategoryModel.model_validate(category) for category in categories]
    finally:
        db.close()


# Meal Plan tools
@mcp.tool()
def create_meal_plan(
    ctx: Context, 
    name: str,
    recipe_ids: List[int] = Field(default_factory=list, description="List of recipe IDs to include in the meal plan")
) -> MealPlanModel:
    """
    Create a new meal plan.
    
    Args:
        ctx: MCP context
        name: Name of the meal plan
        recipe_ids: List of recipe IDs to include in the meal plan
        
    Returns:
        Created meal plan
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Create meal plan schema from request
        meal_plan_schema = schemas.MealPlanCreate(
            name=name,
            recipe_ids=recipe_ids
        )
        
        # Create the meal plan
        meal_plan = crud.create_meal_plan(db, meal_plan=meal_plan_schema)
        
        # Return the created meal plan
        return MealPlanModel.model_validate(meal_plan)
    finally:
        db.close()


@mcp.tool()
def get_meal_plan(ctx: Context, meal_plan_id: int) -> Optional[MealPlanModel]:
    """
    Get a specific meal plan by ID.
    
    Args:
        ctx: MCP context
        meal_plan_id: ID of the meal plan to retrieve
        
    Returns:
        Meal plan details or None if not found
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Get the meal plan
        meal_plan = crud.get_meal_plan(db, meal_plan_id=meal_plan_id)
        
        if meal_plan is None:
            return None
        
        # Return the meal plan
        return MealPlanModel.model_validate(meal_plan)
    finally:
        db.close()


@mcp.tool()
def list_meal_plans(
    ctx: Context, 
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None
) -> MealPlanListResponse:
    """
    List meal plans with optional filtering.
    
    Args:
        ctx: MCP context
        skip: Number of meal plans to skip (for pagination)
        limit: Maximum number of meal plans to return
        search: Optional search term to filter meal plans by name
        
    Returns:
        List of meal plans matching the criteria and total count
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Get meal plans
        meal_plans = crud.get_meal_plans(db, skip=skip, limit=limit, search=search)
        total = crud.count_meal_plans(db, search=search)
        
        # Return the response
        return MealPlanListResponse(meal_plans=meal_plans, total=total)
    finally:
        db.close()


@mcp.tool()
def update_meal_plan(
    ctx: Context, 
    meal_plan_id: int, 
    name: str,
    recipe_ids: List[int] = Field(default_factory=list, description="List of recipe IDs to include in the meal plan")
) -> Optional[MealPlanModel]:
    """
    Update an existing meal plan.
    
    Args:
        ctx: MCP context
        meal_plan_id: ID of the meal plan to update
        name: New name for the meal plan
        recipe_ids: Updated list of recipe IDs to include in the meal plan
        
    Returns:
        Updated meal plan or None if not found
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Create meal plan schema from request
        meal_plan_schema = schemas.MealPlanCreate(
            name=name,
            recipe_ids=recipe_ids
        )
        
        # Update the meal plan
        meal_plan = crud.update_meal_plan(
            db, 
            meal_plan_id=meal_plan_id, 
            meal_plan_data=meal_plan_schema
        )
        
        if meal_plan is None:
            return None
        
        # Return the updated meal plan
        return MealPlanModel.model_validate(meal_plan)
    finally:
        db.close()


@mcp.tool()
def delete_meal_plan(ctx: Context, meal_plan_id: int) -> bool:
    """
    Delete a meal plan.
    
    Args:
        ctx: MCP context
        meal_plan_id: ID of the meal plan to delete
        
    Returns:
        True if meal plan was deleted, False if not found
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Delete the meal plan
        return crud.delete_meal_plan(db, meal_plan_id=meal_plan_id)
    finally:
        db.close()


@mcp.tool()
def get_meal_plan_ingredients(ctx: Context, meal_plan_id: int) -> Optional[List[MealPlanIngredientModel]]:
    """
    Get consolidated ingredients for a meal plan.
    
    Args:
        ctx: MCP context
        meal_plan_id: ID of the meal plan
        
    Returns:
        List of consolidated ingredients or None if meal plan not found
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Get the meal plan
        meal_plan = crud.get_meal_plan(db, meal_plan_id=meal_plan_id)
        
        if meal_plan is None:
            return None
        
        # Return the consolidated ingredients
        return meal_plan.all_ingredients
    finally:
        db.close()


if __name__ == "__main__":
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        debug_print_exception(e)
        raise
