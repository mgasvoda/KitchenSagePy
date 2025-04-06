 # Functions for interacting with the DB

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
import re

from . import models, schemas
from .scrapers.paprika_scraper import scrape_recipe_from_file


def get_category_by_name(db: Session, name: str) -> Optional[models.Category]:
    """Get a category by name or create it if it doesn't exist."""
    return db.query(models.Category).filter(models.Category.name == name).first()


def create_category(db: Session, name: str) -> models.Category:
    """Create a new category."""
    db_category = models.Category(name=name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def get_or_create_category(db: Session, name: str) -> models.Category:
    """Get a category by name or create it if it doesn't exist."""
    db_category = get_category_by_name(db, name)
    if db_category is None:
        db_category = create_category(db, name)
    return db_category


def get_recipe(db: Session, recipe_id: int) -> Optional[models.Recipe]:
    """Get a recipe by ID."""
    return db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()


def get_recipes(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    category: Optional[str] = None,
    ingredient: Optional[str] = None,
    max_total_time: Optional[int] = None
) -> List[models.Recipe]:
    """
    Get all recipes with optional filtering.
    
    Args:
        db: Database session
        skip: Number of recipes to skip (for pagination)
        limit: Maximum number of recipes to return
        search: Optional search term to filter recipes by name
        category: Optional category name to filter recipes
        ingredient: Optional ingredient name to filter recipes
        max_total_time: Optional maximum total time (prep + cook) in minutes
        
    Returns:
        List of recipes matching the criteria
    """
    query = db.query(models.Recipe)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Recipe.name.ilike(search_term),
                models.Recipe.source.ilike(search_term)
            )
        )
    
    # Apply category filter if provided
    if category:
        query = query.join(models.Recipe.categories).filter(
            models.Category.name == category
        )
    
    # Apply ingredient filter if provided
    if ingredient:
        ingredient_term = f"%{ingredient}%"
        query = query.join(models.Recipe.ingredients).filter(
            models.Ingredient.name.ilike(ingredient_term)
        )
    
    # Apply total time filter if provided
    if max_total_time is not None:
        # This is a simplified approach since prep_time and cook_time are stored as strings
        # We'll filter recipes where we can parse the times and their sum is <= max_total_time
        recipes_with_valid_times = []
        all_recipes = query.all()
        
        for recipe in all_recipes:
            total_minutes = 0
            
            # Try to parse prep_time
            if recipe.prep_time:
                prep_minutes = parse_time_to_minutes(recipe.prep_time)
                if prep_minutes is not None:
                    total_minutes += prep_minutes
            
            # Try to parse cook_time
            if recipe.cook_time:
                cook_minutes = parse_time_to_minutes(recipe.cook_time)
                if cook_minutes is not None:
                    total_minutes += cook_minutes
            
            # Include recipe if total time is within limit or if we couldn't parse times
            if total_minutes == 0 or total_minutes <= max_total_time:
                recipes_with_valid_times.append(recipe)
        
        # Apply pagination to filtered recipes
        start_idx = min(skip, len(recipes_with_valid_times))
        end_idx = min(start_idx + limit, len(recipes_with_valid_times))
        return recipes_with_valid_times[start_idx:end_idx]
    
    # Apply pagination
    return query.order_by(models.Recipe.name).offset(skip).limit(limit).all()


def count_recipes(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    ingredient: Optional[str] = None,
    max_total_time: Optional[int] = None
) -> int:
    """Count the total number of recipes matching the filters."""
    query = db.query(models.Recipe)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Recipe.name.ilike(search_term),
                models.Recipe.source.ilike(search_term)
            )
        )
    
    # Apply category filter if provided
    if category:
        query = query.join(models.Recipe.categories).filter(
            models.Category.name == category
        )
    
    # Apply ingredient filter if provided
    if ingredient:
        ingredient_term = f"%{ingredient}%"
        query = query.join(models.Recipe.ingredients).filter(
            models.Ingredient.name.ilike(ingredient_term)
        )
    
    # Apply total time filter if provided
    if max_total_time is not None:
        # This is a simplified approach since prep_time and cook_time are stored as strings
        # We'll count recipes where we can parse the times and their sum is <= max_total_time
        recipes_with_valid_times = []
        all_recipes = query.all()
        
        for recipe in all_recipes:
            total_minutes = 0
            
            # Try to parse prep_time
            if recipe.prep_time:
                prep_minutes = parse_time_to_minutes(recipe.prep_time)
                if prep_minutes is not None:
                    total_minutes += prep_minutes
            
            # Try to parse cook_time
            if recipe.cook_time:
                cook_minutes = parse_time_to_minutes(recipe.cook_time)
                if cook_minutes is not None:
                    total_minutes += cook_minutes
            
            # Include recipe if total time is within limit or if we couldn't parse times
            if total_minutes == 0 or total_minutes <= max_total_time:
                recipes_with_valid_times.append(recipe)
        
        return len(recipes_with_valid_times)
    
    return query.count()


def parse_time_to_minutes(time_str: str) -> Optional[int]:
    """
    Parse a time string (e.g., '1 hour 30 minutes', '45 min') to minutes.
    
    Args:
        time_str: Time string to parse
        
    Returns:
        Total minutes or None if parsing failed
    """
    if not time_str:
        return None
    
    time_str = time_str.lower()
    total_minutes = 0
    
    # Extract hours
    hour_match = re.search(r'(\d+)\s*(?:hour|hr|h)', time_str)
    if hour_match:
        total_minutes += int(hour_match.group(1)) * 60
    
    # Extract minutes
    minute_match = re.search(r'(\d+)\s*(?:minute|min|m)', time_str)
    if minute_match:
        total_minutes += int(minute_match.group(1))
    
    # If no match found, try to parse as just a number (assuming minutes)
    if total_minutes == 0:
        number_match = re.search(r'(\d+)', time_str)
        if number_match:
            total_minutes = int(number_match.group(1))
    
    return total_minutes if total_minutes > 0 else None


def create_recipe(db: Session, recipe: schemas.RecipeCreate) -> models.Recipe:
    """
    Create a new recipe with its ingredients, directions, and categories.
    
    Args:
        db: Database session
        recipe: Recipe data
        
    Returns:
        Created recipe
    """
    # Create the recipe
    db_recipe = models.Recipe(
        name=recipe.name,
        source=recipe.source,
        rating=recipe.rating,
        prep_time=recipe.prep_time,
        cook_time=recipe.cook_time
    )
    
    # Add categories
    for category_name in recipe.categories:
        category = get_or_create_category(db, category_name)
        db_recipe.categories.append(category)
    
    # Add the recipe to the session
    db.add(db_recipe)
    db.flush()  # Flush to get the recipe ID
    
    # Add ingredients
    for i, ingredient_data in enumerate(recipe.ingredients):
        db_ingredient = models.Ingredient(
            recipe_id=db_recipe.id,
            quantity=ingredient_data.quantity,
            unit=ingredient_data.unit,
            name=ingredient_data.name,
            is_header=ingredient_data.is_header
        )
        db.add(db_ingredient)
    
    # Add directions
    for i, direction_data in enumerate(recipe.directions):
        db_direction = models.Direction(
            recipe_id=db_recipe.id,
            step_number=direction_data.step_number,
            description=direction_data.description
        )
        db.add(db_direction)
    
    # Commit all changes
    db.commit()
    db.refresh(db_recipe)
    return db_recipe


def update_recipe(
    db: Session, 
    recipe_id: int, 
    recipe_data: schemas.RecipeCreate
) -> Optional[models.Recipe]:
    """
    Update an existing recipe.
    
    Args:
        db: Database session
        recipe_id: ID of the recipe to update
        recipe_data: New recipe data
        
    Returns:
        Updated recipe or None if recipe not found
    """
    db_recipe = get_recipe(db, recipe_id)
    if db_recipe is None:
        return None
    
    # Update basic recipe data
    db_recipe.name = recipe_data.name
    db_recipe.source = recipe_data.source
    db_recipe.rating = recipe_data.rating
    db_recipe.prep_time = recipe_data.prep_time
    db_recipe.cook_time = recipe_data.cook_time
    
    # Update categories
    db_recipe.categories = []
    for category_name in recipe_data.categories:
        category = get_or_create_category(db, category_name)
        db_recipe.categories.append(category)
    
    # Delete existing ingredients and directions
    db.query(models.Ingredient).filter(models.Ingredient.recipe_id == recipe_id).delete()
    db.query(models.Direction).filter(models.Direction.recipe_id == recipe_id).delete()
    
    # Add new ingredients
    for ingredient_data in recipe_data.ingredients:
        db_ingredient = models.Ingredient(
            recipe_id=recipe_id,
            quantity=ingredient_data.quantity,
            unit=ingredient_data.unit,
            name=ingredient_data.name,
            is_header=ingredient_data.is_header
        )
        db.add(db_ingredient)
    
    # Add new directions
    for direction_data in recipe_data.directions:
        db_direction = models.Direction(
            recipe_id=recipe_id,
            step_number=direction_data.step_number,
            description=direction_data.description
        )
        db.add(db_direction)
    
    # Commit all changes
    db.commit()
    db.refresh(db_recipe)
    return db_recipe


def update_recipe_categories(
    db: Session, 
    recipe_id: int, 
    categories: List[str]
) -> Optional[models.Recipe]:
    """
    Update the categories of an existing recipe.
    
    Args:
        db: Database session
        recipe_id: ID of the recipe to update
        categories: List of category names to assign to the recipe
        
    Returns:
        Updated recipe or None if recipe not found
    """
    # Get the recipe
    db_recipe = get_recipe(db, recipe_id)
    if db_recipe is None:
        return None
    
    # Get existing categories
    existing = db_recipe.categories

    # Add new categories
    for category_name in categories:
        if category_name in existing:
            continue
        # Get or create the category
        category = get_or_create_category(db, category_name)
        db_recipe.categories.append(category)
    
    # Commit changes
    db.commit()
    db.refresh(db_recipe)
    
    return db_recipe


def delete_recipe(db: Session, recipe_id: int) -> bool:
    """
    Delete a recipe.
    
    Args:
        db: Database session
        recipe_id: ID of the recipe to delete
        
    Returns:
        True if recipe was deleted, False if not found
    """
    db_recipe = get_recipe(db, recipe_id)
    if db_recipe is None:
        return False
    
    db.delete(db_recipe)
    db.commit()
    return True


def import_recipe_from_file(db: Session, file_path: str) -> models.Recipe:
    """
    Import a recipe from a Paprika HTML file.
    
    Args:
        db: Database session
        file_path: Path to the HTML file
        
    Returns:
        Imported recipe
    """
    # Scrape the recipe data from the file
    recipe_data = scrape_recipe_from_file(file_path)
    
    # Convert to RecipeCreate schema
    ingredients = []
    for i, ingredient in enumerate(recipe_data["ingredients"]):
        if ingredient["type"] == "header":
            ingredients.append(schemas.IngredientCreate(
                name=ingredient["text"],
                is_header=1
            ))
        else:
            ingredients.append(schemas.IngredientCreate(
                quantity=ingredient["quantity"],
                unit=ingredient["unit"],
                name=ingredient["name"]
            ))
    
    directions = []
    for i, direction in enumerate(recipe_data["directions"]):
        directions.append(schemas.DirectionCreate(
            step_number=i+1,
            description=direction
        ))
    
    recipe = schemas.RecipeCreate(
        name=recipe_data["name"],
        source=recipe_data.get("source"),
        rating=recipe_data["rating"],
        prep_time=recipe_data.get("prep_time"),
        cook_time=recipe_data.get("cook_time"),
        categories=recipe_data["categories"],
        ingredients=ingredients,
        directions=directions
    )
    
    # Create the recipe in the database
    return create_recipe(db, recipe)


# Meal Plan CRUD operations

def get_meal_plan(db: Session, meal_plan_id: int) -> Optional[models.MealPlan]:
    """
    Get a meal plan by ID.
    
    Args:
        db: Database session
        meal_plan_id: ID of the meal plan to retrieve
        
    Returns:
        MealPlan object or None if not found
    """
    return db.query(models.MealPlan).filter(models.MealPlan.id == meal_plan_id).first()


def get_meal_plans(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
) -> List[models.MealPlan]:
    """
    Get all meal plans with optional filtering.
    
    Args:
        db: Database session
        skip: Number of meal plans to skip (for pagination)
        limit: Maximum number of meal plans to return
        search: Optional search term to filter meal plans by name
        
    Returns:
        List of meal plans matching the criteria
    """
    query = db.query(models.MealPlan)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(models.MealPlan.name.ilike(search_term))
    
    # Apply pagination
    return query.order_by(models.MealPlan.created_at.desc()).offset(skip).limit(limit).all()


def count_meal_plans(
    db: Session,
    search: Optional[str] = None
) -> int:
    """
    Count the total number of meal plans matching the filters.
    
    Args:
        db: Database session
        search: Optional search term to filter meal plans by name
        
    Returns:
        Total count of meal plans matching the criteria
    """
    query = db.query(models.MealPlan)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(models.MealPlan.name.ilike(search_term))
    
    return query.count()


def create_meal_plan(db: Session, meal_plan: schemas.MealPlanCreate) -> models.MealPlan:
    """
    Create a new meal plan with its recipes.
    
    Args:
        db: Database session
        meal_plan: Meal plan data
        
    Returns:
        Created meal plan
    """
    # Create the meal plan
    db_meal_plan = models.MealPlan(
        name=meal_plan.name
    )
    
    # Add recipes
    for recipe_id in meal_plan.recipe_ids:
        recipe = get_recipe(db, recipe_id)
        if recipe:
            db_meal_plan.recipes.append(recipe)
    
    # Add the meal plan to the session
    db.add(db_meal_plan)
    db.commit()
    db.refresh(db_meal_plan)
    
    return db_meal_plan


def update_meal_plan(
    db: Session,
    meal_plan_id: int,
    meal_plan_data: schemas.MealPlanCreate
) -> Optional[models.MealPlan]:
    """
    Update an existing meal plan.
    
    Args:
        db: Database session
        meal_plan_id: ID of the meal plan to update
        meal_plan_data: New meal plan data
        
    Returns:
        Updated meal plan or None if meal plan not found
    """
    db_meal_plan = get_meal_plan(db, meal_plan_id)
    if db_meal_plan is None:
        return None
    
    # Update basic meal plan data
    db_meal_plan.name = meal_plan_data.name
    
    # Update recipes
    db_meal_plan.recipes = []
    for recipe_id in meal_plan_data.recipe_ids:
        recipe = get_recipe(db, recipe_id)
        if recipe:
            db_meal_plan.recipes.append(recipe)
    
    # Commit all changes
    db.commit()
    db.refresh(db_meal_plan)
    
    return db_meal_plan


def update_meal_plan_categories(
    db: Session, 
    meal_plan_id: int, 
    categories: List[str]
) -> Optional[models.MealPlan]:
    """
    Update the categories of an existing meal plan.
    
    Args:
        db: Database session
        meal_plan_id: ID of the meal plan to update
        categories: List of category names to assign to the meal plan
        
    Returns:
        Updated meal plan or None if meal plan not found
    """
    # Get the meal plan
    db_meal_plan = get_meal_plan(db, meal_plan_id)
    if db_meal_plan is None:
        return None
    
    # Get existing categories
    existing_categories = [category.name for category in db_meal_plan.categories]
    
    # Add new categories
    for category_name in categories:
        if category_name in existing_categories:
            continue
        # Get or create the category
        category = get_or_create_category(db, category_name)
        db_meal_plan.categories.append(category)
    
    # Commit changes
    db.commit()
    db.refresh(db_meal_plan)
    
    return db_meal_plan


def delete_meal_plan(db: Session, meal_plan_id: int) -> bool:
    """
    Delete a meal plan.
    
    Args:
        db: Database session
        meal_plan_id: ID of the meal plan to delete
        
    Returns:
        True if meal plan was deleted, False if not found
    """
    db_meal_plan = get_meal_plan(db, meal_plan_id)
    if db_meal_plan is None:
        return False
    
    db.delete(db_meal_plan)
    db.commit()
    
    return True