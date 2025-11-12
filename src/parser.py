"""
{
    "step_number": int,
    "description": str,
    "ingredients": [list of ingredient names],
    "tools": [list of tools],
    "methods": [list of methods],
    "time": {
        "duration": str or dict of sub-times,
    },
    "temperature": {
        "oven": str (optional),
        "<ingredient>": str (optional)
    }
}
"""
import json
import re
import sys
from typing import List, Dict


def load_list_from_file(filepath: str) -> List[str]:
    """Load items (ingredients or tools) from a text file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        return []


def extract_ingredients(step: str, ingredients: List[str]) -> List[str]:
    """Return list of ingredient names found in the step."""
    step_lower = step.lower()
    return [i for i in ingredients if i in step_lower]


def extract_tools(step: str, tools: List[str]) -> List[str]:
    """Return list of tools mentioned in the step."""
    step_lower = step.lower()
    return [t for t in tools if t in step_lower]


def extract_methods(step: str) -> List[str]:
    """Extract common cooking methods."""
    common_methods = [
        "bake", "boil", "simmer", "fry", "stir", "mix", "blend", "chop",
        "saute", "roast", "grill", "whisk", "knead", "marinate", "sear",
        "preheat", "steam", "broil"
    ]
    step_lower = step.lower()
    return [m for m in common_methods if re.search(rf"\b{m}\b", step_lower)]


def extract_time(step: str) -> Dict:
    """Extract time information from the step (e.g., 'bake for 20 minutes')."""
    time_pattern = re.compile(r'(\d+)\s*(seconds?|minutes?|hours?)')
    times = time_pattern.findall(step.lower())
    if times:
        total_time = ", ".join([f"{n} {unit}" for n, unit in times])
        return {"duration": total_time}
    return {}


def extract_temperature(step: str, ingredients: List[str]) -> Dict:
    """Extract temperature info (oven or ingredient-specific)."""
    temp_pattern = re.compile(r'(\d{2,3})\s*°\s*[cf]', re.IGNORECASE)
    temps = temp_pattern.findall(step)
    result = {}

    if temps:
        # If oven is mentioned or implied
        if re.search(r'oven', step.lower()):
            result["oven"] = temps[0] + "°"
        else:
            # Try to link to ingredient mentioned near the temp
            for ingredient in ingredients:
                if ingredient in step.lower():
                    result[ingredient] = temps[0] + "°"
                    break
    return result


def parse_step(step_number: int, step: str, ingredients: List[str], tools: List[str]) -> Dict:
    """Parse a single recipe step into a structured dict."""
    step_ingredients = extract_ingredients(step, ingredients)
    step_tools = extract_tools(step, tools)
    methods = extract_methods(step)
    time_info = extract_time(step)
    temp_info = extract_temperature(step, step_ingredients)

    return {
        "step_number": step_number,
        "description": step.strip(),
        "ingredients": step_ingredients,
        "tools": step_tools,
        "methods": methods,
        "time": time_info if time_info else {},
        "temperature": temp_info if temp_info else {}
    }


def main():
    if len(sys.argv) != 4:
        print("Usage: python parser.py ingredients.txt tools.txt 'Step sentence here'") #assumes scraper outputs an ingrediant list
        sys.exit(1)

    ingredients_file = sys.argv[1]
    tools_file = sys.argv[2]
    step_sentence = sys.argv[3]

    ingredients = load_list_from_file(ingredients_file)
    tools = load_list_from_file(tools_file)

    parsed = parse_step(1, step_sentence, ingredients, tools)
    print(json.dumps(parsed, indent=4))


if __name__ == "__main__":
    main()
