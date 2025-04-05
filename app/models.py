# SQLAlchemy models for the database

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from typing import List

Base = declarative_base()

# Association table for many-to-many relationship between recipes and categories
recipe_category = Table(
    "recipe_category",
    Base.metadata,
    Column("recipe_id", Integer, ForeignKey("recipes.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True)
)


class Recipe(Base):
    """Recipe model representing a cooking recipe."""
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    source = Column(String(255), nullable=True)
    rating = Column(Integer, default=0)
    
    # Relationships
    ingredients = relationship("Ingredient", back_populates="recipe", cascade="all, delete-orphan")
    directions = relationship("Direction", back_populates="recipe", order_by="Direction.step_number", cascade="all, delete-orphan")
    categories = relationship("Category", secondary=recipe_category, back_populates="recipes")


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
