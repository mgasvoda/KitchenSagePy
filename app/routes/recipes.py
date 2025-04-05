# API routes for recipe-related endpoints

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/recipes",
    tags=["recipes"],
    responses={404: {"description": "Recipe not found"}}
)


@router.get("/", response_model=schemas.RecipeList)
def read_recipes(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all recipes with optional filtering.
    
    Args:
        skip: Number of recipes to skip (for pagination)
        limit: Maximum number of recipes to return
        search: Optional search term to filter recipes by name
        category: Optional category name to filter recipes
        db: Database session
        
    Returns:
        List of recipes matching the criteria
    """
    recipes = crud.get_recipes(db, skip=skip, limit=limit, search=search, category=category)
    total = crud.count_recipes(db, search=search, category=category)
    return {"recipes": recipes, "total": total}


@router.get("/{recipe_id}", response_model=schemas.Recipe)
def read_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """
    Get a specific recipe by ID.
    
    Args:
        recipe_id: ID of the recipe to retrieve
        db: Database session
        
    Returns:
        Recipe details
        
    Raises:
        HTTPException: If recipe not found
    """
    db_recipe = crud.get_recipe(db, recipe_id=recipe_id)
    if db_recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return db_recipe


@router.post("/", response_model=schemas.Recipe)
def create_recipe(recipe: schemas.RecipeCreate, db: Session = Depends(get_db)):
    """
    Create a new recipe.
    
    Args:
        recipe: Recipe data
        db: Database session
        
    Returns:
        Created recipe
    """
    return crud.create_recipe(db=db, recipe=recipe)


@router.put("/{recipe_id}", response_model=schemas.Recipe)
def update_recipe(
    recipe_id: int, 
    recipe: schemas.RecipeCreate, 
    db: Session = Depends(get_db)
):
    """
    Update an existing recipe.
    
    Args:
        recipe_id: ID of the recipe to update
        recipe: Updated recipe data
        db: Database session
        
    Returns:
        Updated recipe
        
    Raises:
        HTTPException: If recipe not found
    """
    db_recipe = crud.update_recipe(db, recipe_id=recipe_id, recipe_data=recipe)
    if db_recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return db_recipe


@router.delete("/{recipe_id}", response_model=bool)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """
    Delete a recipe.
    
    Args:
        recipe_id: ID of the recipe to delete
        db: Database session
        
    Returns:
        True if recipe was deleted, False if not found
        
    Raises:
        HTTPException: If recipe not found
    """
    result = crud.delete_recipe(db, recipe_id=recipe_id)
    if not result:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return True


@router.get("/categories/", response_model=List[schemas.Category])
def read_categories(db: Session = Depends(get_db)):
    """
    Get all recipe categories.
    
    Args:
        db: Database session
        
    Returns:
        List of all categories
    """
    categories = db.query(models.Category).order_by(models.Category.name).all()
    return categories
