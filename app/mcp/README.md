# KitchenSagePy MCP Server

This directory contains the Model Context Protocol (MCP) server implementation for KitchenSagePy. The MCP server provides a set of tools that allow AI models to interact with the KitchenSagePy database, enabling recipe search, meal plan management, and more.

## Overview

The MCP server exposes a set of tools that can be used by AI models to:

- Search for recipes by name, ingredient, and total time
- Retrieve recipe details
- Get recipe categories
- Create, read, update, and delete meal plans
- Retrieve consolidated ingredients for meal plans

## Available Tools

### Recipe Tools

#### `search_recipes`

Search for recipes with optional filtering by name, ingredient, and total time.

**Parameters:**
- `search`: Optional search term to filter recipes by name
- `category`: Optional category to filter recipes by
- `ingredient`: Optional ingredient to filter recipes by
- `max_total_time`: Optional maximum total time (in minutes) to filter recipes by
- `skip`: Number of recipes to skip (for pagination)
- `limit`: Maximum number of recipes to return

**Returns:**
- List of recipes matching the criteria and total count

#### `get_recipe_by_id`

Get a specific recipe by ID.

**Parameters:**
- `recipe_id`: ID of the recipe to retrieve

**Returns:**
- Recipe details or None if not found

#### `get_categories`

Get all recipe categories.

**Parameters:**
- None

**Returns:**
- List of all categories

### Meal Plan Tools

#### `create_meal_plan`

Create a new meal plan with specified recipes.

**Parameters:**
- `request`: Meal plan creation request with:
  - `name`: Name of the meal plan
  - `recipe_ids`: List of recipe IDs to include in the meal plan

**Returns:**
- Created meal plan with consolidated ingredients

#### `get_meal_plan`

Get a specific meal plan by ID.

**Parameters:**
- `meal_plan_id`: ID of the meal plan to retrieve

**Returns:**
- Meal plan details or None if not found

#### `list_meal_plans`

List meal plans with optional filtering.

**Parameters:**
- `skip`: Number of meal plans to skip (for pagination)
- `limit`: Maximum number of meal plans to return
- `search`: Optional search term to filter meal plans by name

**Returns:**
- List of meal plans matching the criteria and total count

#### `update_meal_plan`

Update an existing meal plan.

**Parameters:**
- `meal_plan_id`: ID of the meal plan to update
- `request`: Meal plan update request with:
  - `name`: Name of the meal plan
  - `recipe_ids`: List of recipe IDs to include in the meal plan

**Returns:**
- Updated meal plan or None if not found

#### `delete_meal_plan`

Delete a meal plan.

**Parameters:**
- `meal_plan_id`: ID of the meal plan to delete

**Returns:**
- True if meal plan was deleted, False if not found

#### `get_meal_plan_ingredients`

Get consolidated ingredients for a meal plan.

**Parameters:**
- `meal_plan_id`: ID of the meal plan

**Returns:**
- List of consolidated ingredients or None if meal plan not found

## Data Models

### Recipe Models

- `RecipeModel`: Represents a recipe with ingredients, directions, and categories
- `IngredientModel`: Represents a recipe ingredient with name, quantity, and unit
- `DirectionModel`: Represents a recipe direction with step number and text
- `CategoryModel`: Represents a recipe category with name
- `RecipeSearchRequest`: Request model for recipe search
- `RecipeSearchResponse`: Response model for recipe search

### Meal Plan Models

- `MealPlanModel`: Represents a meal plan with recipes and consolidated ingredients
- `MealPlanIngredientModel`: Represents a consolidated ingredient in a meal plan
- `MealPlanCreateRequest`: Request model for creating a meal plan
- `MealPlanUpdateRequest`: Request model for updating a meal plan
- `MealPlanListResponse`: Response model for meal plan list

## Usage Example

Here's an example of how an AI model might use these tools:

```python
# Search for recipes containing "chicken"
recipes = search_recipes(ctx, RecipeSearchRequest(search="chicken"))

# Create a meal plan with the first two chicken recipes
recipe_ids = [recipes.recipes[0].id, recipes.recipes[1].id]
meal_plan = create_meal_plan(ctx, MealPlanCreateRequest(
    name="Chicken Meal Plan",
    recipe_ids=recipe_ids
))

# Get the consolidated ingredients for the meal plan
ingredients = get_meal_plan_ingredients(ctx, meal_plan.id)
```

## Implementation Details

The MCP server is implemented using FastMCP, a library for building MCP servers with FastAPI. It uses the same database models and CRUD operations as the REST API, ensuring consistency across different interfaces to the application.

Each tool follows the same pattern:
1. Gets a database session from the MCP context
2. Uses the session to call the appropriate CRUD function
3. Converts the result to the appropriate Pydantic model
4. Returns the result to the caller

## Adding New Tools

To add a new tool to the MCP server:

1. Define any necessary request/response models using Pydantic
2. Implement the tool function with the `@mcp.tool()` decorator
3. Document the tool in this README

## Running the MCP Server

The MCP server is automatically started when the main FastAPI application is run. It shares the same database connection and models as the REST API.
