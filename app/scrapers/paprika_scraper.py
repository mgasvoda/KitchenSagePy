from typing import Dict, List, Optional
import re
from bs4 import BeautifulSoup
from pathlib import Path


class PaprikaRecipeScraper:
    """
    Scraper for extracting recipe data from Paprika HTML format.
    """
    
    def __init__(self, html_content: str):
        """
        Initialize the scraper with HTML content.
        
        Args:
            html_content: The HTML content of the recipe
        """
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.recipe_div = self.soup.find('div', {'class': 'recipe'})
        
    def extract_recipe(self) -> Dict:
        """
        Extract all recipe data from the HTML.
        
        Returns:
            Dict containing all recipe information
        """
        if not self.recipe_div:
            raise ValueError("No recipe found in the provided HTML")
            
        recipe_data = {
            "name": self._extract_name(),
            "rating": self._extract_rating(),
            "categories": self._extract_categories(),
            "source": self._extract_source(),
            "ingredients": self._extract_ingredients(),
            "directions": self._extract_directions(),
        }
        
        return recipe_data
    
    def _extract_name(self) -> str:
        """Extract the recipe name."""
        name_element = self.recipe_div.find('h1', {'class': 'name'})
        return name_element.text.strip() if name_element else ""
    
    def _extract_rating(self) -> int:
        """Extract the recipe rating (number of stars)."""
        rating_element = self.recipe_div.find('p', {'class': 'rating'})
        if not rating_element:
            return 0
            
        # Count the number of star characters or get the value attribute
        if 'value' in rating_element.attrs:
            return int(rating_element['value'])
        else:
            # Count star characters
            return rating_element.text.count('★')
    
    def _extract_categories(self) -> List[str]:
        """Extract recipe categories."""
        categories_element = self.recipe_div.find('p', {'class': 'categories'})
        if not categories_element:
            return []
            
        # Categories might be comma-separated
        categories_text = categories_element.text.strip()
        return [cat.strip() for cat in categories_text.split(',')]
    
    def _extract_source(self) -> Optional[str]:
        """Extract the recipe source."""
        source_element = self.recipe_div.find('span', {'itemprop': 'author'})
        return source_element.text.strip() if source_element else None
    
    def _extract_ingredients(self) -> List[Dict]:
        """
        Extract recipe ingredients.
        
        Returns:
            List of ingredient dictionaries with quantity, unit, and name
        """
        ingredients_div = self.recipe_div.find('div', {'class': 'ingredients'})
        if not ingredients_div:
            return []
            
        ingredient_elements = ingredients_div.find_all('p', {'class': 'line', 'itemprop': 'recipeIngredient'})
        ingredients = []
        
        for element in ingredient_elements:
            text = element.text.strip()
            
            # Skip section headers (elements without strong tags)
            if not element.find('strong') and len(text) < 30:
                # This is likely a section header
                if text:  # Only add non-empty headers
                    ingredients.append({
                        "type": "header",
                        "text": text
                    })
                continue
                
            # Parse ingredient with quantity
            quantity = ""
            strong_tag = element.find('strong')
            if strong_tag:
                quantity = strong_tag.text.strip()
                # Remove the quantity part from the text
                text = text.replace(quantity, "", 1).strip()
            
            # Try to separate unit from ingredient name
            parts = text.split(" ", 1)
            unit = parts[0] if len(parts) > 1 and len(parts[0]) < 10 else ""
            name = parts[1] if len(parts) > 1 and unit else text
            
            ingredients.append({
                "type": "ingredient",
                "quantity": quantity,
                "unit": unit,
                "name": name.strip()
            })
            
        return ingredients
    
    def _extract_directions(self) -> List[str]:
        """Extract cooking directions as a list of steps."""
        directions_div = self.recipe_div.find('div', {'itemprop': 'recipeInstructions'})
        if not directions_div:
            return []
            
        direction_elements = directions_div.find_all('p', {'class': 'line'})
        directions = [element.text.strip() for element in direction_elements]
        
        return directions


def scrape_recipe_from_file(file_path: str) -> Dict:
    """
    Scrape a recipe from a Paprika HTML file.
    
    Args:
        file_path: Path to the HTML file
        
    Returns:
        Dict containing the recipe data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    scraper = PaprikaRecipeScraper(html_content)
    return scraper.extract_recipe()