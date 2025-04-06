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


@mcp.tool()
def update_recipe(
    ctx: Context, 
    recipe_id: Optional[int] = None,
    request: mcp_models.RecipeUpdateRequest = None,
    # Individual parameters for backward compatibility and convenience
    name: Optional[str] = None,
    source: Optional[str] = None,
    rating: Optional[int] = None,
    prep_time: Optional[str] = None,
    cook_time: Optional[str] = None,
    categories: Optional[List[str]] = None,
    ingredients: Optional[List[mcp_models.IngredientCreateModel]] = None,
    directions: Optional[List[mcp_models.DirectionCreateModel]] = None,
    update_categories_only: bool = False
) -> Optional[mcp_models.RecipeModel]:
    """
    Create or update a recipe with ingredients, directions, and categories.
    
    This function combines the functionality of create_recipe and update_recipe_categories.
    If recipe_id is provided, it updates an existing recipe; otherwise, it creates a new one.
    
    Args:
        ctx: MCP context
        recipe_id: ID of the recipe to update (None for create)
        request: Recipe update request object (alternative to individual parameters)
        name: Name of the recipe
        source: Source of the recipe (e.g., website, cookbook)
        rating: Rating of the recipe (0-5)
        prep_time: Preparation time (e.g., '10 minutes')
        cook_time: Cooking time (e.g., '30 minutes')
        categories: List of category names for the recipe
        ingredients: List of ingredients with quantity, unit, name, and is_header flag
        directions: List of directions with step_number and description
        update_categories_only: If true, only update the categories
        
    Returns:
        Created or updated recipe, or None if update fails
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Use request object if provided, otherwise use individual parameters
        if request is not None:
            name = request.name if name is None else name
            source = request.source if source is None else source
            rating = request.rating if rating is None else rating
            prep_time = request.prep_time if prep_time is None else prep_time
            cook_time = request.cook_time if cook_time is None else cook_time
            categories = request.categories if categories is None else categories
            ingredients = request.ingredients if ingredients is None else ingredients
            directions = request.directions if directions is None else directions
            update_categories_only = request.update_categories_only if update_categories_only is False else update_categories_only
        
        # Handle categories-only update
        if recipe_id is not None and update_categories_only:
            if categories is None:
                categories = []
            recipe = crud.update_recipe_categories(
                db, 
                recipe_id=recipe_id, 
                categories=categories
            )
            
            if recipe is None:
                return None
            
            # Return the updated recipe
            return mcp_models.RecipeModel.model_validate(recipe)
        
        # For full update or create, we need all the required fields
        if recipe_id is None and name is None:
            raise ValueError("Name is required when creating a new recipe")
        
        # Convert MCP models to schema models for ingredients and directions
        schema_ingredients = []
        if ingredients is not None:
            schema_ingredients = [
                schemas.IngredientCreate(
                    quantity=ingredient.quantity,
                    unit=ingredient.unit,
                    name=ingredient.name,
                    is_header=ingredient.is_header
                ) for ingredient in ingredients
            ]
        
        schema_directions = []
        if directions is not None:
            schema_directions = [
                schemas.DirectionCreate(
                    step_number=direction.step_number,
                    description=direction.description
                ) for direction in directions
            ]
        
        # Create recipe schema
        recipe_schema = schemas.RecipeCreate(
            name=name if name is not None else "",
            source=source,
            rating=rating if rating is not None else 0,
            prep_time=prep_time,
            cook_time=cook_time,
            categories=categories if categories is not None else [],
            ingredients=schema_ingredients,
            directions=schema_directions
        )
        
        # Create or update the recipe
        if recipe_id is None:
            # Create new recipe
            recipe = crud.create_recipe(db, recipe=recipe_schema)
        else:
            # Update existing recipe
            recipe = crud.update_recipe(db, recipe_id=recipe_id, recipe_data=recipe_schema)
            
            if recipe is None:
                return None
        
        # Return the created/updated recipe
        return mcp_models.RecipeModel.model_validate(recipe)
    finally:
        db.close()


@mcp.tool()
def get_recipes(
    ctx: Context,
    request: mcp_models.RecipeGetRequest
) -> mcp_models.RecipeGetResponse:
    """
    Get recipes with flexible filtering and column selection.
    
    This function combines search functionality with the ability to select
    which columns are returned in the response. It can be used to:
    1. Get a specific recipe by ID
    2. Search recipes by name, ingredient, category, or time
    3. Control which fields are returned in the response
    
    Args:
        ctx: MCP context
        request: Recipe get request with filtering options and column selection
        
    Returns:
        List of recipes matching the criteria with selected columns and total count
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        if request.id is not None:
            # Get a specific recipe by ID
            recipe = crud.get_recipe(db, recipe_id=request.id)
            recipes = [recipe] if recipe else []
            total = 1 if recipe else 0
        else:
            # Search for recipes with filters
            recipes = crud.get_recipes(
                db=db,
                skip=request.skip,
                limit=request.limit,
                search=request.name,
                category=request.category,
                ingredient=request.ingredient,
                max_total_time=request.max_total_time
            )
            
            # Get the total count
            total = crud.count_recipes(
                db=db,
                search=request.name,
                category=request.category,
                ingredient=request.ingredient,
                max_total_time=request.max_total_time
            )
        
        # Create dynamic models with only the requested columns
        dynamic_recipes = []
        for recipe in recipes:
            recipe_dict = {}
            
            # Add basic fields if requested
            for field in request.columns:
                if field in ["id", "name", "source", "rating", "prep_time", "cook_time", "description", "notes"]:
                    recipe_dict[field] = getattr(recipe, field, None)
            
            # Add related fields if requested
            if "ingredients" in request.columns:
                recipe_dict["ingredients"] = [
                    mcp_models.IngredientModel.model_validate(ingredient)
                    for ingredient in recipe.ingredients
                ]
            
            if "directions" in request.columns:
                recipe_dict["directions"] = [
                    mcp_models.DirectionModel.model_validate(direction)
                    for direction in recipe.directions
                ]
            
            if "categories" in request.columns:
                recipe_dict["categories"] = [
                    mcp_models.CategoryModel.model_validate(category)
                    for category in recipe.categories
                ]
            
            dynamic_recipes.append(mcp_models.DynamicRecipeModel(**recipe_dict))
        
        # Return the response
        return mcp_models.RecipeGetResponse(recipes=dynamic_recipes, total=total)
    finally:
        db.close()


@mcp.tool()
def get_meal_plans(
    ctx: Context,
    request: mcp_models.MealPlanGetRequest
) -> mcp_models.MealPlanGetResponse:
    """
    Get meal plans with flexible filtering and column selection.
    
    This function combines search functionality with the ability to select
    which columns are returned in the response. It can be used to:
    1. Get a specific meal plan by ID
    2. Search meal plans by name
    3. Control which fields are returned in the response
    4. Optionally include related recipes and consolidated ingredients
    
    Args:
        ctx: MCP context
        request: Meal plan get request with filtering options and column selection
        
    Returns:
        List of meal plans matching the criteria with selected columns and total count
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        if request.id is not None:
            # Get a specific meal plan by ID
            meal_plan = crud.get_meal_plan(db, meal_plan_id=request.id)
            meal_plans = [meal_plan] if meal_plan else []
            total = 1 if meal_plan else 0
        else:
            # Search for meal plans with filters
            meal_plans = crud.get_meal_plans(
                db=db,
                skip=request.skip,
                limit=request.limit,
                search=request.name
            )
            
            # Get the total count
            total = crud.count_meal_plans(
                db=db,
                search=request.name
            )
        
        # Create dynamic models with only the requested columns
        dynamic_meal_plans = []
        for meal_plan in meal_plans:
            meal_plan_dict = {}
            
            # Add basic fields if requested
            for field in request.columns:
                if field in ["id", "name", "created_at"]:
                    meal_plan_dict[field] = getattr(meal_plan, field, None)
            
            # Add categories if requested
            if "categories" in request.columns:
                meal_plan_dict["categories"] = [
                    mcp_models.CategoryModel.model_validate(category)
                    for category in meal_plan.categories
                ]
            
            # Add recipes if requested
            if request.include_recipes:
                meal_plan_dict["recipes"] = [
                    mcp_models.RecipeModel.model_validate(recipe)
                    for recipe in meal_plan.recipes
                ]
            
            # Add consolidated ingredients if requested
            if request.include_ingredients:
                meal_plan_dict["all_ingredients"] = [
                    mcp_models.MealPlanIngredientModel(**ingredient)
                    for ingredient in meal_plan.all_ingredients
                ]
            
            dynamic_meal_plans.append(mcp_models.DynamicMealPlanModel(**meal_plan_dict))
        
        # Return the response
        return mcp_models.MealPlanGetResponse(meal_plans=dynamic_meal_plans, total=total)
    finally:
        db.close()


if __name__ == "__main__":
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        debug_print_exception(e)
        raise
