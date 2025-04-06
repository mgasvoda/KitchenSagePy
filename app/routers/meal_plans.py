from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List
from sqlalchemy.orm import Session
import datetime

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

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
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
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
async def get_meal_plan(
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
