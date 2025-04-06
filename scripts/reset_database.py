# Reset and initialize the database with all required tables
import os
import sys
from sqlalchemy import inspect

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, SessionLocal, Base
from app.models import (
    Recipe, Ingredient, Direction, Category, MealPlan,
    recipe_category, meal_plan_recipe, meal_plan_category
)

def reset_database():
    """Drop all tables and recreate them."""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables after creation
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("\nAvailable tables after creation:")
    for table in tables:
        print(f"- {table}")
        columns = inspector.get_columns(table)
        for column in columns:
            print(f"  - {column['name']} ({column['type']})")

def create_sample_data():
    """Create sample data for testing."""
    db = SessionLocal()
    try:
        # Check if we already have data
        existing_recipes = db.query(Recipe).all()
        if existing_recipes:
            print(f"Found {len(existing_recipes)} existing recipes. Skipping sample data creation.")
            return
            
        print("Creating sample categories...")
        categories = [
            Category(name="Breakfast"),
            Category(name="Lunch"),
            Category(name="Dinner"),
            Category(name="Dessert"),
            Category(name="Vegetarian")
        ]
        db.add_all(categories)
        db.commit()
        
        print("Creating sample recipes...")
        recipes = [
            {
                "name": "Pancakes",
                "source": "Grandma's cookbook",
                "rating": 5,
                "prep_time": "10 minutes",
                "cook_time": "15 minutes",
                "categories": [categories[0], categories[4]],  # Breakfast, Vegetarian
                "ingredients": [
                    {"name": "Flour", "quantity": "2", "unit": "cups"},
                    {"name": "Milk", "quantity": "1", "unit": "cup"},
                    {"name": "Eggs", "quantity": "2", "unit": ""},
                    {"name": "Sugar", "quantity": "2", "unit": "tbsp"},
                    {"name": "Baking Powder", "quantity": "1", "unit": "tbsp"}
                ],
                "directions": [
                    {"step_number": 1, "description": "Mix dry ingredients."},
                    {"step_number": 2, "description": "Add wet ingredients and mix until smooth."},
                    {"step_number": 3, "description": "Cook on a hot griddle until bubbles form."},
                    {"step_number": 4, "description": "Flip and cook until golden brown."}
                ]
            },
            {
                "name": "Pasta Carbonara",
                "source": "Italian cookbook",
                "rating": 4,
                "prep_time": "15 minutes",
                "cook_time": "20 minutes",
                "categories": [categories[1], categories[2]],  # Lunch, Dinner
                "ingredients": [
                    {"name": "Spaghetti", "quantity": "1", "unit": "pound"},
                    {"name": "Bacon", "quantity": "8", "unit": "slices"},
                    {"name": "Eggs", "quantity": "4", "unit": ""},
                    {"name": "Parmesan Cheese", "quantity": "1", "unit": "cup"},
                    {"name": "Black Pepper", "quantity": "1", "unit": "tsp"}
                ],
                "directions": [
                    {"step_number": 1, "description": "Cook pasta according to package directions."},
                    {"step_number": 2, "description": "Cook bacon until crispy."},
                    {"step_number": 3, "description": "Beat eggs and cheese together."},
                    {"step_number": 4, "description": "Toss hot pasta with egg mixture and bacon."}
                ]
            },
            {
                "name": "Chocolate Chip Cookies",
                "source": "Family recipe",
                "rating": 5,
                "prep_time": "20 minutes",
                "cook_time": "12 minutes",
                "categories": [categories[3]],  # Dessert
                "ingredients": [
                    {"name": "Flour", "quantity": "2.25", "unit": "cups"},
                    {"name": "Butter", "quantity": "1", "unit": "cup"},
                    {"name": "Brown Sugar", "quantity": "0.75", "unit": "cup"},
                    {"name": "White Sugar", "quantity": "0.75", "unit": "cup"},
                    {"name": "Chocolate Chips", "quantity": "2", "unit": "cups"}
                ],
                "directions": [
                    {"step_number": 1, "description": "Cream butter and sugars."},
                    {"step_number": 2, "description": "Add eggs and vanilla."},
                    {"step_number": 3, "description": "Mix in dry ingredients."},
                    {"step_number": 4, "description": "Fold in chocolate chips."},
                    {"step_number": 5, "description": "Bake at 375°F for 10-12 minutes."}
                ]
            }
        ]
        
        for recipe_data in recipes:
            recipe = Recipe(
                name=recipe_data["name"],
                source=recipe_data["source"],
                rating=recipe_data["rating"],
                prep_time=recipe_data["prep_time"],
                cook_time=recipe_data["cook_time"]
            )
            
            # Add categories
            for category in recipe_data["categories"]:
                recipe.categories.append(category)
            
            # Add ingredients
            for ingredient_data in recipe_data["ingredients"]:
                ingredient = Ingredient(
                    name=ingredient_data["name"],
                    quantity=ingredient_data["quantity"],
                    unit=ingredient_data["unit"]
                )
                recipe.ingredients.append(ingredient)
            
            # Add directions
            for direction_data in recipe_data["directions"]:
                direction = Direction(
                    step_number=direction_data["step_number"],
                    description=direction_data["description"]
                )
                recipe.directions.append(direction)
            
            db.add(recipe)
        
        db.commit()
        print(f"Created {len(recipes)} sample recipes.")
        
        # Create meal plans
        print("Creating sample meal plans...")
        all_recipes = db.query(Recipe).all()
        
        meal_plans = [
            {
                "name": "Weekly Dinner Plan",
                "recipes": [all_recipes[0], all_recipes[1]],
                "categories": [categories[0], categories[2]]  # Breakfast, Dinner
            },
            {
                "name": "Healthy Lunch Options",
                "recipes": [all_recipes[1]],
                "categories": [categories[1], categories[4]]  # Lunch, Vegetarian
            },
            {
                "name": "Weekend Brunch",
                "recipes": [all_recipes[0], all_recipes[2]],
                "categories": [categories[0], categories[3]]  # Breakfast, Dessert
            }
        ]
        
        for meal_plan_data in meal_plans:
            meal_plan = MealPlan(name=meal_plan_data["name"])
            
            # Add recipes
            for recipe in meal_plan_data["recipes"]:
                meal_plan.recipes.append(recipe)
            
            # Add categories
            for category in meal_plan_data["categories"]:
                meal_plan.categories.append(category)
            
            db.add(meal_plan)
        
        db.commit()
        print(f"Created {len(meal_plans)} sample meal plans.")
        
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()
    create_sample_data()
    print("Database reset and initialized successfully.")
