"""
MCP server implementation for KitchenSagePy recipe search functionality.
Allows searching recipes by name, ingredient, and total time.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from mcp.server.fastmcp import Context, FastMCP
from typing import Optional, List
from pydantic import Field

import sys
import os
import traceback

# Handle imports for both direct execution and module import
try:
    # Try relative imports first (when imported as a module)
    from .. import models, crud, schemas
    from ..database import SessionLocal, engine
    import mcp_models
except ImportError:
    # Fall back to absolute imports (when run directly)
    # Add the project root to sys.path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from app import models, crud, schemas
    from app.database import SessionLocal, engine
    from app.mcp import mcp_models


# Create a named server
mcp = FastMCP("KitchenSagePy")

def debug_print_exception(e: Exception):
    print("Exception during startup:", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)



@mcp.tool()
def search_recipes(
    ctx: Context, 
    name: Optional[str] = None,
    ingredient: Optional[str] = None,
    category: Optional[str] = None,
    max_total_time: Optional[int] = None,
    skip: int = 0,
    limit: int = 10
) -> mcp_models.RecipeSearchResponse:
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
            mcp_models.SimpleRecipeModel(
                id=recipe.id,
                name=recipe.name,
                rating=recipe.rating,
                prep_time=recipe.prep_time,
                cook_time=recipe.cook_time,
                ingredients=recipe.ingredients,
                categories=recipe.categories
            ) for recipe in recipes
        ]
        
        # Return the response
        return mcp_models.RecipeSearchResponse(recipes=simple_recipes, total=total)
    finally:
        db.close()


@mcp.tool()
def get_recipe_by_id(ctx: Context, recipe_id: int) -> Optional[mcp_models.RecipeModel]:
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
        
        return mcp_models.RecipeModel.model_validate(recipe)
    finally:
        db.close()


@mcp.tool()
def get_categories(ctx: Context) -> List[mcp_models.CategoryModel]:
    """
    Get all recipe categories. These may include meal types (i.e. dinner, snack, etc.), cuisines, seasons, or other groupings.
    
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
        return [mcp_models.CategoryModel.model_validate(category) for category in categories]
    finally:
        db.close()


# Meal Plan tools
@mcp.tool()
def create_meal_plan(
    ctx: Context, 
    name: str,
    recipe_ids: List[int] = Field(default_factory=list, description="List of recipe IDs to include in the meal plan")
) -> mcp_models.MealPlanModel:
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
        return mcp_models.MealPlanModel.model_validate(meal_plan)
    finally:
        db.close()


@mcp.tool()
def get_meal_plan(ctx: Context, meal_plan_id: int) -> Optional[mcp_models.MealPlanModel]:
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
        return mcp_models.MealPlanModel.model_validate(meal_plan)
    finally:
        db.close()


@mcp.tool()
def list_meal_plans(
    ctx: Context, 
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None
) -> mcp_models.MealPlanListResponse:
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
        return mcp_models.MealPlanListResponse(meal_plans=meal_plans, total=total)
    finally:
        db.close()


@mcp.tool()
def update_meal_plan(
    ctx: Context, 
    meal_plan_id: int, 
    name: str,
    recipe_ids: List[int] = Field(default_factory=list, description="List of recipe IDs to include in the meal plan")
) -> Optional[mcp_models.MealPlanModel]:
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
        return mcp_models.MealPlanModel.model_validate(meal_plan)
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
def get_meal_plan_ingredients(ctx: Context, meal_plan_id: int) -> Optional[List[mcp_models.MealPlanIngredientModel]]:
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


@mcp.tool()
def update_recipe_categories(
    ctx: Context, 
    recipe_id: int,
    categories: List[str] = Field(default_factory=list, description="List of category names to assign to the recipe")
) -> Optional[mcp_models.RecipeModel]:
    """
    Update the categories of an existing recipe.
    
    Args:
        ctx: MCP context
        recipe_id: ID of the recipe to update
        categories: List of category names to assign to the recipe
        
    Returns:
        Updated recipe or None if not found
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Update the recipe categories
        recipe = crud.update_recipe_categories(
            db, 
            recipe_id=recipe_id, 
            categories=categories
        )
        
        if recipe is None:
            return None
        
        # Return the updated recipe
        return mcp_models.RecipeModel.model_validate(recipe)
    finally:
        db.close()


@mcp.tool()
def update_meal_plan_categories(
    ctx: Context, 
    meal_plan_id: int,
    categories: List[str] = Field(default_factory=list, description="List of category names to assign to the meal plan")
) -> Optional[mcp_models.MealPlanModel]:
    """
    Update the categories of an existing meal plan.
    
    Args:
        ctx: MCP context
        meal_plan_id: ID of the meal plan to update
        categories: List of category names to assign to the meal plan
        
    Returns:
        Updated meal plan or None if not found
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Update the meal plan categories
        meal_plan = crud.update_meal_plan_categories(
            db, 
            meal_plan_id=meal_plan_id, 
            categories=categories
        )
        
        if meal_plan is None:
            return None
        
        # Return the updated meal plan
        return mcp_models.MealPlanModel.model_validate(meal_plan)
    finally:
        db.close()


if __name__ == "__main__":
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        debug_print_exception(e)
        raise
