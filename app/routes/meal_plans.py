# API routes for meal plan-related endpoints

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
import math

from .. import crud, models, schemas
from ..database import get_db

# Set up API router
api_router = APIRouter(
    prefix="/api/meal-plans",
    tags=["meal-plans"],
    responses={404: {"description": "Meal plan not found"}}
)

# Set up web router
router = APIRouter()

# Set up templates
templates = Jinja2Templates(directory="app/templates")


# API Routes

@api_router.get("/", response_model=schemas.MealPlanList)
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


@api_router.get("/{meal_plan_id}", response_model=schemas.MealPlan)
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


@api_router.post("/", response_model=schemas.MealPlan)
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


@api_router.put("/{meal_plan_id}", response_model=schemas.MealPlan)
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


@api_router.delete("/{meal_plan_id}", response_model=bool)
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


@api_router.get("/{meal_plan_id}/ingredients", response_model=List[schemas.MealPlanIngredient])
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


# Web Routes

@router.get("/meal-plans", response_class=HTMLResponse)
async def list_meal_plans(
    request: Request,
    skip: int = Query(0, alias="skip"),
    limit: int = Query(10, alias="limit"),
    query: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Display the meal plans page with optional filtering and pagination.
    """
    # Get meal plans with filtering
    meal_plans = crud.get_meal_plans(db, skip=skip, limit=limit, search=query)
    total = crud.count_meal_plans(db, search=query)
    
    # Apply category filter if provided
    if category:
        # Filter meal plans by category
        meal_plans = [mp for mp in meal_plans if any(cat.name == category for cat in mp.categories)]
        total = len(meal_plans)
    
    # Get all categories for sidebar
    categories = db.query(models.Category).order_by(models.Category.name).all()
    
    # Calculate pagination
    current_page = (skip // limit) + 1
    total_pages = math.ceil(total / limit) if total > 0 else 1
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "meal_plans": meal_plans,
            "total": total,
            "categories": categories,
            "selected_category": category,
            "query": query,
            "skip": skip,
            "limit": limit,
            "current_page": current_page,
            "total_pages": total_pages,
            "active_section": "meal_plans",
            "current_year": datetime.datetime.now().year
        }
    )

@router.get("/meal-plan/{meal_plan_id}", response_class=HTMLResponse)
async def meal_plan_detail(
    request: Request,
    meal_plan_id: int,
    db: Session = Depends(get_db)
):
    """
    Display a specific meal plan with its recipes and grocery list.
    """
    # Get the meal plan
    meal_plan = crud.get_meal_plan(db, meal_plan_id=meal_plan_id)
    
    if meal_plan is None:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    return templates.TemplateResponse(
        "meal_plan.html",
        {
            "request": request,
            "meal_plan": meal_plan,
            "current_year": datetime.datetime.now().year
        }
    )
