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
        return [mcp_models.CategoryModel.model_validate(category, from_attributes=True) for category in categories]
    finally:
        db.close()


# Meal Plan tools
@mcp.tool()
def update_meal_plan(
    ctx: Context, 
    meal_plan_id: Optional[int] = Field(
        default=None,
        description="The ID of the meal plan to update. If null/None, a new meal plan will be created."
    ),
    request: mcp_models.MealPlanUpdateRequest = Field(
        description="An object containing the details for the meal plan update or creation. See the MealPlanUpdateRequest schema for full details of each field."
    )
) -> Optional[mcp_models.MealPlanModel]:
    """
    Create or update a meal plan with recipes and categories.
    
    This function creates a new meal plan or updates an existing one based on the provided request object.
    If meal_plan_id is provided, it updates an existing meal plan; otherwise, it creates a new one.
    
    Args:
        ctx: MCP context
        meal_plan_id: ID of the meal plan to update (None for create)
        request: Meal plan update request object containing name, recipe_ids, categories, and update flags
        
    Returns:
        Created or updated meal plan, or None if update fails
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Extract values from request object
        name = request.name
        recipe_ids = request.recipe_ids
        categories = request.categories
        update_categories_only = request.update_categories_only
        
        # Handle categories-only update
        if meal_plan_id is not None and update_categories_only:
            if categories is None:
                categories = []
            meal_plan = crud.update_meal_plan_categories(
                db, 
                meal_plan_id=meal_plan_id, 
                categories=categories
            )
            
            if meal_plan is None:
                return None
            
            # Return the updated meal plan
            return mcp_models.MealPlanModel.model_validate(meal_plan, from_attributes=True)
        
        # For full update or create, we need all the required fields
        if meal_plan_id is None and name is None:
            raise ValueError("Name is required when creating a new meal plan")
        
        # Ensure all categories exist in the database before creating/updating the meal plan
        processed_categories = None
        if categories is not None:
            processed_categories = []
            for category_name in categories:
                # This will create the category if it doesn't exist
                crud.get_or_create_category(db, category_name)
                processed_categories.append(category_name)
        
        # Create meal plan schema
        meal_plan_schema = schemas.MealPlanCreate(
            name=name if name is not None else "",
            recipe_ids=recipe_ids if recipe_ids is not None else []
        )
        
        # Create or update the meal plan
        if meal_plan_id is None:
            # Create new meal plan
            meal_plan = crud.create_meal_plan(db, meal_plan=meal_plan_schema)
        else:
            # Update existing meal plan
            meal_plan = crud.update_meal_plan(
                db, 
                meal_plan_id=meal_plan_id, 
                meal_plan_data=meal_plan_schema
            )
            
            if meal_plan is None:
                return None
            
            # Update categories if provided
            if processed_categories is not None:
                meal_plan = crud.update_meal_plan_categories(
                    db, 
                    meal_plan_id=meal_plan_id, 
                    categories=processed_categories
                )
                
                if meal_plan is None:
                    return None
        
        # Return the created/updated meal plan
        return mcp_models.MealPlanModel.model_validate(meal_plan, from_attributes=True)
    finally:
        db.close()


@mcp.tool()
def update_recipe(
    ctx: Context, 
    recipe_id: Optional[int] = Field(
        default=None,
        description="The ID of the recipe to update. If null/None, a new recipe will be created."
    ),
    request: mcp_models.RecipeUpdateRequest = Field(
        description="An object containing the details for the recipe update or creation. See the RecipeUpdateRequest schema for full details of each field."
    )
) -> Optional[mcp_models.RecipeModel]:
    """
    Create or update a recipe with ingredients, directions, and categories.
    
    This function creates a new recipe or updates an existing one based on the provided request object.
    If recipe_id is provided, it updates an existing recipe; otherwise, it creates a new one.
    
    Args:
        ctx: MCP context
        recipe_id: ID of the recipe to update (None for create)
        request: Recipe update request object containing name, source, rating, times, categories, ingredients, and directions
        
    Returns:
        Created or updated recipe, or None if update fails
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Extract values from request object
        name = request.name
        source = request.source
        rating = request.rating
        prep_time = request.prep_time
        cook_time = request.cook_time
        categories = request.categories
        ingredients = request.ingredients
        directions = request.directions
        update_categories_only = request.update_categories_only
        
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
            return mcp_models.RecipeModel.model_validate(recipe, from_attributes=True)
        
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
        
        # Ensure all categories exist in the database before creating the recipe schema
        processed_categories = []
        if categories is not None:
            for category_name in categories:
                # This will create the category if it doesn't exist
                crud.get_or_create_category(db, category_name)
                processed_categories.append(category_name)
        
        # Create recipe schema
        recipe_schema = schemas.RecipeCreate(
            name=name if name is not None else "",
            source=source,
            rating=rating if rating is not None else 0,
            prep_time=prep_time,
            cook_time=cook_time,
            categories=processed_categories if processed_categories else [],
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
        return mcp_models.RecipeModel.model_validate(recipe, from_attributes=True)
    finally:
        db.close()


@mcp.tool()
def get_recipes(
    ctx: Context,
    request: mcp_models.RecipeGetRequest = Field(
        description="An object containing the search parameters and column selection options. See the RecipeGetRequest schema for full details of each field."
    )
) -> mcp_models.RecipeGetResponse:
    """
    Get recipes with flexible filtering and column selection.
    
    This function allows searching for recipes with various filters and selecting
    which columns are returned in the response. It can be used to:
    1. Get a specific recipe by ID
    2. Search recipes by name or source
    3. Filter recipes by ingredient
    4. Filter recipes by category
    5. Filter recipes by total time
    
    Args:
        ctx: MCP context
        request: Recipe get request object containing search parameters and column selection options
        
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
                ingredient=request.ingredient,
                category=request.category,
                max_total_time=request.max_total_time
            )
            
            # Get the total count
            total = crud.count_recipes(
                db=db,
                search=request.name,
                ingredient=request.ingredient,
                category=request.category,
                max_total_time=request.max_total_time
            )
        
        # Create dynamic models with only the requested columns
        dynamic_recipes = []
        for recipe in recipes:
            if recipe is None:
                continue
                
            recipe_dict = {}
            
            # Add basic fields if requested
            for field in request.columns:
                if field in ["id", "name", "source", "rating", "prep_time", "cook_time", "description", "notes"]:
                    recipe_dict[field] = getattr(recipe, field, None)
            
            # Add related fields if requested
            if "ingredients" in request.columns and hasattr(recipe, "ingredients"):
                recipe_dict["ingredients"] = [
                    mcp_models.IngredientModel.model_validate(ingredient, from_attributes=True)
                    for ingredient in recipe.ingredients
                ]
            
            if "directions" in request.columns and hasattr(recipe, "directions"):
                recipe_dict["directions"] = [
                    mcp_models.DirectionModel.model_validate(direction, from_attributes=True)
                    for direction in recipe.directions
                ]
            
            if "categories" in request.columns and hasattr(recipe, "categories"):
                recipe_dict["categories"] = [
                    mcp_models.CategoryModel.model_validate(category, from_attributes=True)
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
    request: mcp_models.MealPlanGetRequest = Field(
        description="An object containing the search parameters and column selection options. See the MealPlanGetRequest schema for full details of each field."
    )
) -> mcp_models.MealPlanGetResponse:
    """
    Get meal plans with flexible filtering and column selection.
    
    This function allows searching for meal plans with various filters and selecting
    which columns are returned in the response. It can be used to:
    1. Get a specific meal plan by ID
    2. Search meal plans by name
    3. Control which fields are returned in the response
    4. Optionally include related recipes and consolidated ingredients
    
    Args:
        ctx: MCP context
        request: Meal plan get request object containing search parameters and column selection options
        
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
            if meal_plan is None:
                continue
                
            meal_plan_dict = {}
            
            # Add basic fields if requested
            for field in request.columns:
                if field in ["id", "name", "created_at"]:
                    meal_plan_dict[field] = getattr(meal_plan, field, None)
            
            # Add categories if requested
            if "categories" in request.columns and hasattr(meal_plan, "categories"):
                meal_plan_dict["categories"] = [
                    mcp_models.CategoryModel.model_validate(category, from_attributes=True)
                    for category in meal_plan.categories
                ]
            
            # Add recipes if requested
            if "recipes" in request.columns and request.include_recipes and hasattr(meal_plan, "recipes"):
                recipe_list = []
                for recipe in meal_plan.recipes:
                    recipe_dict = {
                        "id": recipe.id,
                        "name": recipe.name,
                        "source": recipe.source,
                        "rating": recipe.rating,
                        "prep_time": recipe.prep_time,
                        "cook_time": recipe.cook_time
                    }
                    
                    # Include ingredients if requested
                    if request.include_ingredients and hasattr(recipe, "ingredients"):
                        recipe_dict["ingredients"] = [
                            mcp_models.IngredientModel.model_validate(ingredient, from_attributes=True)
                            for ingredient in recipe.ingredients
                        ]
                    
                    # Include categories if requested
                    if hasattr(recipe, "categories"):
                        recipe_dict["categories"] = [
                            mcp_models.CategoryModel.model_validate(category, from_attributes=True)
                            for category in recipe.categories
                        ]
                    
                    recipe_list.append(mcp_models.RecipeModel.model_validate(recipe_dict, from_attributes=True))
                
                meal_plan_dict["recipes"] = recipe_list
            
            # Add consolidated ingredients if requested
            if "all_ingredients" in request.columns and request.include_ingredients and hasattr(meal_plan, "all_ingredients"):
                meal_plan_dict["all_ingredients"] = [
                    mcp_models.MealPlanIngredientModel.model_validate(ingredient, from_attributes=True)
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
