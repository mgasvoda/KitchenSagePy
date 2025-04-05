"""
MCP server implementation for KitchenSagePy recipe search functionality.
Allows searching recipes by name, ingredient, and total time.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from .. import models, crud
from ..database import SessionLocal, engine

# Create a named server
mcp = FastMCP("KitchenSagePy")


@dataclass
class AppContext:
    """Application context for the MCP server."""
    db_session_maker: Any  # SessionLocal


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context."""
    # Initialize on startup - using the existing database connection
    try:
        # We're using the existing SessionLocal for synchronous SQLAlchemy
        yield AppContext(db_session_maker=SessionLocal)
    finally:
        # No cleanup needed as we're using the existing database connection
        pass


# Pass lifespan to server
mcp = FastMCP("KitchenSagePy", lifespan=app_lifespan)


# Define request and response models
class RecipeSearchRequest(BaseModel):
    """Request model for recipe search."""
    search: Optional[str] = Field(None, description="Search term for recipe name or source")
    ingredient: Optional[str] = Field(None, description="Ingredient to search for")
    category: Optional[str] = Field(None, description="Category to filter by")
    max_total_time: Optional[int] = Field(None, description="Maximum total time (prep + cook) in minutes")
    skip: int = Field(0, description="Number of recipes to skip (for pagination)")
    limit: int = Field(100, description="Maximum number of recipes to return")


class IngredientModel(BaseModel):
    """Response model for ingredient."""
    id: int
    quantity: Optional[str] = None
    unit: Optional[str] = None
    name: str
    is_header: int = 0

    class Config:
        orm_mode = True


class DirectionModel(BaseModel):
    """Response model for direction."""
    id: int
    step_number: int
    description: str

    class Config:
        orm_mode = True


class CategoryModel(BaseModel):
    """Response model for category."""
    id: int
    name: str

    class Config:
        orm_mode = True


class RecipeModel(BaseModel):
    """Response model for recipe."""
    id: int
    name: str
    source: Optional[str] = None
    rating: int = 0
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    ingredients: List[IngredientModel] = []
    directions: List[DirectionModel] = []
    categories: List[CategoryModel] = []

    class Config:
        orm_mode = True


class RecipeSearchResponse(BaseModel):
    """Response model for recipe search."""
    recipes: List[RecipeModel]
    total: int


@mcp.tool()
def search_recipes(ctx: Context, request: RecipeSearchRequest) -> RecipeSearchResponse:
    """
    Search for recipes with optional filtering by name, ingredient, and total time.
    
    Args:
        ctx: MCP context
        request: Search parameters
        
    Returns:
        List of recipes matching the criteria and total count
    """
    # Get database session from context
    db_session_maker = ctx.request_context.lifespan_context.db_session_maker
    
    # Use the session in a context manager
    with db_session_maker() as db:
        # Call the existing CRUD function to search for recipes
        recipes = crud.get_recipes(
            db=db,
            skip=request.skip,
            limit=request.limit,
            search=request.search,
            category=request.category,
            ingredient=request.ingredient,
            max_total_time=request.max_total_time
        )
        
        # Get the total count
        total = crud.count_recipes(
            db=db,
            search=request.search,
            category=request.category,
            ingredient=request.ingredient,
            max_total_time=request.max_total_time
        )
        
        # Return the response
        return RecipeSearchResponse(recipes=recipes, total=total)


@mcp.tool()
def get_recipe_by_id(ctx: Context, recipe_id: int) -> Optional[RecipeModel]:
    """
    Get a specific recipe by ID.
    
    Args:
        ctx: MCP context
        recipe_id: ID of the recipe to retrieve
        
    Returns:
        Recipe details or None if not found
    """
    # Get database session from context
    db_session_maker = ctx.request_context.lifespan_context.db_session_maker
    
    # Use the session in a context manager
    with db_session_maker() as db:
        # Call the existing CRUD function to get the recipe
        recipe = crud.get_recipe(db, recipe_id=recipe_id)
        
        if recipe is None:
            return None
        
        return RecipeModel.from_orm(recipe)


@mcp.tool()
def get_categories(ctx: Context) -> List[CategoryModel]:
    """
    Get all recipe categories.
    
    Args:
        ctx: MCP context
        
    Returns:
        List of all categories
    """
    # Get database session from context
    db_session_maker = ctx.request_context.lifespan_context.db_session_maker
    
    # Use the session in a context manager
    with db_session_maker() as db:
        # Query all categories
        categories = db.query(models.Category).order_by(models.Category.name).all()
        
        # Convert to response model
        return [CategoryModel.from_orm(category) for category in categories]
