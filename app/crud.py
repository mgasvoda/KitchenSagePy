 # Functions for interacting with the DB

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

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
    category: Optional[str] = None
) -> List[models.Recipe]:
    """
    Get all recipes with optional filtering.
    
    Args:
        db: Database session
        skip: Number of recipes to skip (for pagination)
        limit: Maximum number of recipes to return
        search: Optional search term to filter recipes by name
        category: Optional category name to filter recipes
        
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
    
    # Apply pagination
    return query.order_by(models.Recipe.name).offset(skip).limit(limit).all()


def count_recipes(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None
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
    
    return query.count()


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
        rating=recipe.rating
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
        source=recipe_data["source"],
        rating=recipe_data["rating"],
        categories=recipe_data["categories"],
        ingredients=ingredients,
        directions=directions
    )
    
    # Create the recipe in the database
    return create_recipe(db, recipe)