#!/usr/bin/env python
"""
Test script for the Paprika recipe scraper and database integration.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models import Base
from app.scrapers.paprika_scraper import scrape_recipe_from_file
from app.crud import import_recipe_from_file


def setup_database():
    """Set up an in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_recipe_scraper(file_path: str):
    """Test the recipe scraper on a file."""
    print(f"Testing recipe scraper on {file_path}")
    print("-" * 50)
    
    # Scrape the recipe
    recipe_data = scrape_recipe_from_file(file_path)
    
    # Print the extracted data
    print(f"Recipe Name: {recipe_data['name']}")
    print(f"Rating: {recipe_data['rating']} stars")
    print(f"Source: {recipe_data['source']}")
    print(f"Categories: {', '.join(recipe_data['categories'])}")
    
    print("\nIngredients:")
    for ingredient in recipe_data["ingredients"]:
        if ingredient["type"] == "header":
            print(f"  -- {ingredient['text']} --")
        else:
            quantity = ingredient["quantity"] if ingredient["quantity"] else ""
            unit = ingredient["unit"] if ingredient["unit"] else ""
            name = ingredient["name"]
            print(f"  {quantity} {unit} {name}".strip())
    
    print("\nDirections:")
    for i, step in enumerate(recipe_data["directions"], 1):
        print(f"  {i}. {step}")
    
    return recipe_data


def test_database_import(db: Session, file_path: str):
    """Test importing a recipe into the database."""
    print("\nTesting database import")
    print("-" * 50)
    
    # Import the recipe
    recipe = import_recipe_from_file(db, file_path)
    
    # Print the imported recipe
    print(f"Imported Recipe: {recipe.name}")
    print(f"Rating: {recipe.rating} stars")
    print(f"Source: {recipe.source}")
    print(f"Categories: {', '.join(c.name for c in recipe.categories)}")
    
    print("\nIngredients:")
    for ingredient in recipe.ingredients:
        if ingredient.is_header:
            print(f"  -- {ingredient.name} --")
        else:
            quantity = ingredient.quantity if ingredient.quantity else ""
            unit = ingredient.unit if ingredient.unit else ""
            name = ingredient.name
            print(f"  {quantity} {unit} {name}".strip())
    
    print("\nDirections:")
    for direction in sorted(recipe.directions, key=lambda d: d.step_number):
        print(f"  {direction.step_number}. {direction.description}")
    
    return recipe


def main():
    """Main entry point for the test script."""
    # Path to the test recipe
    recipe_path = os.path.join("dev", "dev", "Recipes", "Antoni Falafel Salad.html")
    
    # Make sure the file exists
    if not os.path.exists(recipe_path):
        print(f"Error: Recipe file not found at {recipe_path}")
        return
    
    # Test the scraper
    recipe_data = test_recipe_scraper(recipe_path)
    
    # Test the database import
    db = setup_database()
    try:
        recipe = test_database_import(db, recipe_path)
    finally:
        db.close()
    
    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    main()
