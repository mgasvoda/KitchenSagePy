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
from app.database import engine
from app.models import Base, MealPlan, meal_plan_recipe, Recipe

def main():
    """Initialize the meal_plans table and related association table."""
    print("Initializing meal_plans and meal_plan_recipe tables...")
    
    # Check if tables exist before creating them
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"Existing tables: {existing_tables}")
    
    # Create all tables (including meal_plans and meal_plan_recipe)
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

if __name__ == "__main__":
    main()
