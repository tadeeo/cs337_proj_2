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
import spacy
from spacy.matcher import Matcher
from rapidfuzz import process, fuzz

nlp = spacy.load("en_core_web_sm")

COOKING_VERBS = ["mix", "bake", "grill", "stir", "preheat", "add", "chop",
                 "saute", "boil", "fry", "sprinkle", "layer", "remove",
                 "pour", "place", "cook"]

ingredient_set = {}
tools_list = ["bowl", "pan", "skillet", "oven", "spatula", "dish", "grate", "foil", "pot"]


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
    
    HEAT_REGEX = re.compile(
        r"""
        \b
        (?:over|on|to|at)?\s*
        (?:
            (?P<low>low|very\s+low) |
            (?P<med_low>med(?:ium)?[-\s]?low) |
            (?P<med_high>med(?:ium)?[-\s]?high) |
            (?P<medium>med(?:ium)?) |
            (?P<high>high|very\s+high)
        )
        (?:[-\s]?heat)?
        \b
        """,
        re.IGNORECASE | re.VERBOSE
    )

    match = HEAT_REGEX.search(step)
    if match:
        for level, value in match.groupdict().items():
            if value:
                result["stove/burner"] = level.upper()
                break

    return result

def parse_step(step_number: int, step: str, ingredients: List[str], tools: List[str]) -> Dict:
    """Parse a single recipe step into a structured dict."""
    step_ingredients = extract_ingredients(step, ingredients)
    step_tools = extract_tools(step, tools)
    methods = extract_methods(step)
    time_info = extract_time(step)
    temp_info = extract_temperature(step, step_ingredients)

    # add structured action tags using spaCy
    actions = extract_actions_rule_based(step, ingredients, COOKING_VERBS, step_tools)

    return {
        "step_number": step_number,
        "description": step.strip(),
        "actions": actions,
        "time": time_info if time_info else {},
        "temperature": temp_info if temp_info else {}
    }


def extract_actions_rule_based(text, ingredients, cooking_verbs, tools_list):
    matcher = Matcher(nlp.vocab)
    doc = nlp(text)
    actions = []
    print(matcher(doc))
    
    ingredients_found = find_ingredients_in_text(text, ingredients, matcher)
    tools_found = [tool for tool in tools_list if tool in text.lower()]

    for token in doc:
        verb_lemma = token.lemma_.lower()
        if verb_lemma in cooking_verbs:
            actions.append({
                "verb": verb_lemma,
                "ingredients": ingredients_found,
                "tool": tools_found[0] if tools_found else None
            })

    return actions

def normalize_ingredient(name: str) -> str:
    # Lowercase
    name = name.lower()
    # Remove things like "shredded", "chopped", "(16 ounce) package", "or to taste"
    name = re.sub(r'\([^)]*\)', '', name)        # remove parenthesis
    name = re.sub(r'\b(shredded|chopped|diced|sliced|fresh|lean|ground)\b', '', name)
    name = re.sub(r'or to taste|to taste', '', name)
    name = re.sub(r'\,|\.', '', name)
    name = re.sub(r'\s+', ' ', name)            # normalize spaces
    return name.strip()

def find_ingredients_in_text(text, ingredients, matcher):
    COMMON_INGREDIENTS = {"water", "salt", "pepper", "oil", "butter"}
    ingredient_set = set(normalize_ingredient(ing) for ing in ingredients) | COMMON_INGREDIENTS
    
    step_lower = text.lower()

    matches = []
    for ingredient in ingredient_set:
        ingredient_lower = ingredient.lower()

        # Fuzzy match the ingredient against the step text
        score = fuzz.partial_ratio(ingredient_lower, step_lower)

        if score >= 70:
            matches.append((ingredient, score))
            print(ingredient + " " + str(score))

    # Sort by descending match strength
    matches.sort(key=lambda x: x[1], reverse=True)

    # Return only the ingredient names
    
    # return [m[0] for m in matches]
    # text_lower = text.lower()
    # found = []
    
    # for ing in ingredient_set:
    #     # ing_tokens = [t for t in re.findall(r"\b\w+\b", ing)]
    #     # print(ing_tokens)
    #     # match_count = sum(1 for t in ing_tokens if t in text_lower)
    #     # if match_count / len(ing_tokens) >= 0.25:  # at least quarter of the tokens match
    #     #     found.append(ing)
    #     pattern = [{"TEXT": {"FUZZY": {"IN": ing}}}]
    #     matcher.add(text_lower, [pattern])
    # return found


def main():
    if len(sys.argv) != 4:
        print("Usage: python parser.py ingredients.txt tools.txt 'Step sentence here'") #assumes scraper outputs an ingrediant list
        sys.exit(1)

    ingredients_file = sys.argv[1]
    tools_file = sys.argv[2]
    step_sentence = sys.argv[3]

    with open("recipe.json", "r") as f:
        data = json.load(f)

    ingredients = [item["name"] for item in data["ingredients"]]
    print("*********ingredients:", ingredients)

    #ingredients = load_list_from_file(ingredients_file)
    tools = load_list_from_file(tools_file)

    parsed = parse_step(1, step_sentence, ingredients, tools)
    print(json.dumps(parsed, indent=4))


if __name__ == "__main__":
    main()
