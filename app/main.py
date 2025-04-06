from datetime import datetime
from fastapi import FastAPI, Request, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import math

from . import crud, models, schemas
from .database import get_db, init_db
from .routes import recipes, meal_plans

# Initialize FastAPI app
app = FastAPI(title="KitchenSage")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Include API routes
app.include_router(recipes.router)
app.include_router(meal_plans.router)
app.include_router(meal_plans.api_router)

# Initialize database
init_db()

@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request, 
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 12
):
    """
    Home page route that displays all recipes with pagination.
    """
    recipes = crud.get_recipes(db, skip=skip, limit=limit)
    total = crud.count_recipes(db)
    categories = db.query(models.Category).order_by(models.Category.name).all()
    
    total_pages = math.ceil(total / limit) if total > 0 else 1
    current_page = skip // limit + 1 if skip > 0 else 1
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "recipes": recipes,
            "total": total,
            "skip": skip,
            "limit": limit,
            "categories": categories,
            "current_page": current_page,
            "total_pages": total_pages,
            "current_year": datetime.now().year
        }
    )

@app.get("/search")
async def search_recipes(
    request: Request,
    query: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 12,
    db: Session = Depends(get_db)
):
    """
    Search recipes by name or filter by category.
    """
    recipes = crud.get_recipes(db, skip=skip, limit=limit, search=query, category=category)
    total = crud.count_recipes(db, search=query, category=category)
    categories = db.query(models.Category).order_by(models.Category.name).all()
    
    total_pages = math.ceil(total / limit) if total > 0 else 1
    current_page = skip // limit + 1 if skip > 0 else 1
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "recipes": recipes,
            "total": total,
            "skip": skip,
            "limit": limit,
            "query": query,
            "selected_category": category,
            "categories": categories,
            "current_page": current_page,
            "total_pages": total_pages,
            "current_year": datetime.now().year
        }
    )

@app.get("/recipe/{recipe_id}", response_class=HTMLResponse)
async def recipe_detail(
    request: Request,
    recipe_id: int,
    db: Session = Depends(get_db)
):
    """
    Display a single recipe by ID.
    """
    recipe = crud.get_recipe(db, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return templates.TemplateResponse(
        "recipe.html", 
        {
            "request": request,
            "recipe": recipe,
            "current_year": datetime.now().year
        }
    )
