# Define request and response models
class RecipeSearchRequest(BaseModel):
    """Request model for recipe search."""
    name: Optional[str] = Field(None, description="Search term for recipe name")
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
        from_attributes = True


class DirectionModel(BaseModel):
    """Response model for direction."""
    id: int
    step_number: int
    description: str

    class Config:
        from_attributes = True


class CategoryModel(BaseModel):
    """Response model for category."""
    id: int
    name: str

    class Config:
        from_attributes = True


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
        from_attributes = True


class SimpleRecipeModel(BaseModel):
    """Simplified response model for recipe with only essential fields."""
    id: int
    name: str
    rating: int = 0
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None

    class Config:
        from_attributes = True


class RecipeSearchResponse(BaseModel):
    """Response model for recipe search."""
    recipes: List[SimpleRecipeModel]
    total: int


class MealPlanIngredientModel(BaseModel):
    """Model for consolidated ingredients in a meal plan."""
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None


class MealPlanModel(BaseModel):
    """Response model for meal plan."""
    id: int
    name: str
    created_at: datetime
    recipes: List[RecipeModel] = []
    all_ingredients: List[MealPlanIngredientModel] = []

    class Config:
        from_attributes = True


class MealPlanCreateRequest(BaseModel):
    """Request model for creating a meal plan."""
    name: str
    recipe_ids: List[int] = Field([], description="List of recipe IDs to include in the meal plan")


class MealPlanUpdateRequest(BaseModel):
    """Request model for updating a meal plan."""
    name: str
    recipe_ids: List[int] = Field([], description="List of recipe IDs to include in the meal plan")


class MealPlanListResponse(BaseModel):
    """Response model for meal plan list."""
    meal_plans: List[MealPlanModel]
    total: int


class RecipeCategoryUpdateRequest(BaseModel):
    """Request model for updating recipe categories."""
    categories: List[str] = Field([], description="List of category names to assign to the recipe")


class MealPlanCategoryUpdateRequest(BaseModel):
    """Request model for updating meal plan categories."""
    categories: List[str] = Field([], description="List of category names to assign to the meal plan")
