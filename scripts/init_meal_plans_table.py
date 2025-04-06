#!/usr/bin/env python
"""
Script to initialize the meal_plans table in the SQLite database.
This ensures the table exists and has the correct schema.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import all necessary components
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import Base, MealPlan, meal_plan_recipe, meal_plan_category, Recipe, Category

def create_sample_meal_plans(db: Session):
    """Create sample meal plans with recipes and categories."""
    print("Creating sample meal plans...")
    
    # Check if we already have meal plans
    existing_meal_plans = db.query(MealPlan).all()
    if existing_meal_plans:
        print(f"Found {len(existing_meal_plans)} existing meal plans. Skipping sample data creation.")
        return
    
    # Get existing recipes
    recipes = db.query(Recipe).all()
    if not recipes:
        print("No recipes found. Please run the recipe initialization script first.")
        return
    
    # Get existing categories
    categories = db.query(Category).all()
    if not categories:
        print("No categories found. Please run the category initialization script first.")
        return
    
    # Create sample meal plans
    meal_plans = [
        {
            "name": "Weekly Dinner Plan",
            "recipe_indices": [0, 1, 2, 3, 4],  # Use first 5 recipes
            "category_indices": [0, 1]  # Use first 2 categories
        },
        {
            "name": "Healthy Lunch Options",
            "recipe_indices": [2, 5, 7],  # Mix of recipes
            "category_indices": [2, 3]
        },
        {
            "name": "Weekend Brunch",
            "recipe_indices": [1, 3, 6],
            "category_indices": [0, 4]
        }
    ]
    
    for meal_plan_data in meal_plans:
        meal_plan = MealPlan(name=meal_plan_data["name"])
        
        # Add recipes
        for idx in meal_plan_data["recipe_indices"]:
            if idx < len(recipes):
                meal_plan.recipes.append(recipes[idx])
        
        # Add categories
        for idx in meal_plan_data["category_indices"]:
            if idx < len(categories):
                meal_plan.categories.append(categories[idx])
        
        db.add(meal_plan)
    
    db.commit()
    print(f"Created {len(meal_plans)} sample meal plans successfully.")

def main():
    """Initialize the meal_plans table and related association tables."""
    print("Initializing meal_plans, meal_plan_recipe, and meal_plan_category tables...")
    
    # Check if tables exist before creating them
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"Existing tables: {existing_tables}")
    
    # Create all tables (including meal_plans and related association tables)
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    
    # Verify tables after creation
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("\nAvailable tables after creation:")
    for table in tables:
        print(f"- {table}")
        columns = inspector.get_columns(table)
        for column in columns:
            print(f"  - {column['name']} ({column['type']})")
    
    # Create sample meal plans
    db = SessionLocal()
    try:
        create_sample_meal_plans(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()
