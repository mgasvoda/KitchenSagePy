#!/usr/bin/env python
"""
Recipe importer script for KitchenSage.
This script demonstrates how to use the Paprika scraper to import recipes into the database.
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.crud import import_recipe_from_file


def setup_database(db_url: str):
    """Set up the database and return a session factory."""
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal


def import_recipe(db_session, file_path: str):
    """Import a recipe from a file into the database."""
    try:
        recipe = import_recipe_from_file(db_session, file_path)
        print(f"Successfully imported recipe: {recipe.name}")
        print(f"- Rating: {recipe.rating} stars")
        print(f"- Source: {recipe.source}")
        print(f"- Categories: {', '.join(c.name for c in recipe.categories)}")
        print(f"- {len(recipe.ingredients)} ingredients")
        print(f"- {len(recipe.directions)} directions")
        return True
    except Exception as e:
        print(f"Error importing recipe: {e}")
        return False


def main():
    """Main entry point for the script."""
    # Set up the database
    db_url = "sqlite:///./kitchen_sage.db"
    SessionLocal = setup_database(db_url)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python import_recipe.py <path_to_recipe_html> [<path_to_recipe_html> ...]")
        return
    
    # Iterate through all provided files and directories
    success_count = 0
    for path in sys.argv[1:]:
        if os.path.isfile(path):
            # If a file, just import it
            print(f"Importing recipe from {path}...")
            db = SessionLocal()
            try:
                if import_recipe(db, path):
                    success_count += 1
            finally:
                db.close()
        elif os.path.isdir(path):
            # If a directory, iterate through all .html files and import them
            for file_path in Path(path).glob('*.html'):
                print(f"Importing recipe from {file_path.resolve()}...")
                db = SessionLocal()
                try:
                    if import_recipe(db, str(file_path.resolve())):
                        success_count += 1
                finally:
                    db.close()
        else:
            print(f"File not found: {path}")
    
    print(f"Import complete. Successfully imported {success_count} of {len(sys.argv) - 1} recipes.")


if __name__ == "__main__":
    main()
