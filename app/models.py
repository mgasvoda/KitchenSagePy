# SQLAlchemy models for the database

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Table, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from typing import List
import datetime

Base = declarative_base()

# Association table for many-to-many relationship between recipes and categories
recipe_category = Table(
    "recipe_category",
    Base.metadata,
    Column("recipe_id", Integer, ForeignKey("recipes.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True)
)

# Association table for many-to-many relationship between meal plans and recipes
meal_plan_recipe = Table(
    "meal_plan_recipe",
    Base.metadata,
    Column("meal_plan_id", Integer, ForeignKey("meal_plans.id"), primary_key=True),
    Column("recipe_id", Integer, ForeignKey("recipes.id"), primary_key=True)
)

# Association table for many-to-many relationship between meal plans and categories
meal_plan_category = Table(
    "meal_plan_category",
    Base.metadata,
    Column("meal_plan_id", Integer, ForeignKey("meal_plans.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True)
)


class Recipe(Base):
    """Recipe model representing a cooking recipe."""
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    source = Column(String(255), nullable=True)
    rating = Column(Integer, default=0)
    prep_time = Column(String(50), nullable=True)
    cook_time = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    ingredients = relationship("Ingredient", back_populates="recipe", cascade="all, delete-orphan")
    directions = relationship("Direction", back_populates="recipe", order_by="Direction.step_number", cascade="all, delete-orphan")
    categories = relationship("Category", secondary=recipe_category, back_populates="recipes")
    meal_plans = relationship("MealPlan", secondary=meal_plan_recipe, back_populates="recipes")


class Ingredient(Base):
    """Ingredient model representing a recipe ingredient."""
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    quantity = Column(String(50), nullable=True)
    unit = Column(String(50), nullable=True)
    name = Column(String(255))
    is_header = Column(Integer, default=0)  # 0 = ingredient, 1 = section header
    
    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")


class Direction(Base):
    """Direction model representing a recipe step."""
    __tablename__ = "directions"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    step_number = Column(Integer)
    description = Column(Text)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="directions")


class Category(Base):
    """Category model for recipe classification."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    
    # Relationships
    recipes = relationship("Recipe", secondary=recipe_category, back_populates="categories")
    meal_plans = relationship("MealPlan", secondary=meal_plan_category, back_populates="categories")


class MealPlan(Base):
    """MealPlan model representing a collection of recipes for a meal plan."""
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    recipes = relationship("Recipe", secondary=meal_plan_recipe, back_populates="meal_plans")
    categories = relationship("Category", secondary=meal_plan_category, back_populates="meal_plans")
    
    @property
    def all_ingredients(self) -> List[dict]:
        """
        Get a consolidated list of all ingredients from all recipes in the meal plan.
        
        Returns:
            List of dictionaries containing ingredient information
        """
        ingredients_dict = {}
        
        for recipe in self.recipes:
            for ingredient in recipe.ingredients:
                # Skip section headers
                if ingredient.is_header:
                    continue
                
                # Create a key based on ingredient name and unit for grouping
                key = (ingredient.name.lower(), ingredient.unit)
                
                if key in ingredients_dict:
                    # Try to add quantities if they exist and are numeric
                    if ingredient.quantity and ingredient.quantity.isdigit():
                        if ingredients_dict[key]["quantity"] and ingredients_dict[key]["quantity"].isdigit():
                            ingredients_dict[key]["quantity"] = str(
                                float(ingredients_dict[key]["quantity"]) + float(ingredient.quantity)
                            )
                else:
                    ingredients_dict[key] = {
                        "name": ingredient.name,
                        "quantity": ingredient.quantity,
                        "unit": ingredient.unit
                    }
        
        # Convert dict to list
        return list(ingredients_dict.values())
