# API routes for meal plan-related endpoints

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/meal-plans",
    tags=["meal-plans"],
    responses={404: {"description": "Meal plan not found"}}
)


@router.get("/", response_model=schemas.MealPlanList)
def read_meal_plans(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all meal plans with optional filtering.
    
    Args:
        skip: Number of meal plans to skip (for pagination)
        limit: Maximum number of meal plans to return
        search: Optional search term to filter meal plans by name
        db: Database session
        
    Returns:
        List of meal plans matching the criteria
    """
    meal_plans = crud.get_meal_plans(db, skip=skip, limit=limit, search=search)
    total = crud.count_meal_plans(db, search=search)
    return {"meal_plans": meal_plans, "total": total}


@router.get("/{meal_plan_id}", response_model=schemas.MealPlan)
def read_meal_plan(meal_plan_id: int, db: Session = Depends(get_db)):
    """
    Get a specific meal plan by ID.
    
    Args:
        meal_plan_id: ID of the meal plan to retrieve
        db: Database session
        
    Returns:
        Meal plan details
        
    Raises:
        HTTPException: If meal plan not found
    """
    db_meal_plan = crud.get_meal_plan(db, meal_plan_id=meal_plan_id)
    if db_meal_plan is None:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return db_meal_plan


@router.post("/", response_model=schemas.MealPlan)
def create_meal_plan(meal_plan: schemas.MealPlanCreate, db: Session = Depends(get_db)):
    """
    Create a new meal plan.
    
    Args:
        meal_plan: Meal plan data
        db: Database session
        
    Returns:
        Created meal plan
    """
    return crud.create_meal_plan(db=db, meal_plan=meal_plan)


@router.put("/{meal_plan_id}", response_model=schemas.MealPlan)
def update_meal_plan(
    meal_plan_id: int, 
    meal_plan: schemas.MealPlanCreate, 
    db: Session = Depends(get_db)
):
    """
    Update an existing meal plan.
    
    Args:
        meal_plan_id: ID of the meal plan to update
        meal_plan: Updated meal plan data
        db: Database session
        
    Returns:
        Updated meal plan
        
    Raises:
        HTTPException: If meal plan not found
    """
    db_meal_plan = crud.update_meal_plan(db, meal_plan_id=meal_plan_id, meal_plan_data=meal_plan)
    if db_meal_plan is None:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return db_meal_plan


@router.delete("/{meal_plan_id}", response_model=bool)
def delete_meal_plan(meal_plan_id: int, db: Session = Depends(get_db)):
    """
    Delete a meal plan.
    
    Args:
        meal_plan_id: ID of the meal plan to delete
        db: Database session
        
    Returns:
        True if meal plan was deleted, False if not found
        
    Raises:
        HTTPException: If meal plan not found
    """
    result = crud.delete_meal_plan(db, meal_plan_id=meal_plan_id)
    if not result:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return True


@router.get("/{meal_plan_id}/ingredients", response_model=List[schemas.MealPlanIngredient])
def read_meal_plan_ingredients(meal_plan_id: int, db: Session = Depends(get_db)):
    """
    Get all ingredients for a specific meal plan.
    
    Args:
        meal_plan_id: ID of the meal plan
        db: Database session
        
    Returns:
        List of consolidated ingredients for the meal plan
        
    Raises:
        HTTPException: If meal plan not found
    """
    db_meal_plan = crud.get_meal_plan(db, meal_plan_id=meal_plan_id)
    if db_meal_plan is None:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    return db_meal_plan.all_ingredients
