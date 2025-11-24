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

NON_ACTIONABLE_PATTERNS = [ #includes patterns for observation, warning, and advice
    "be careful", "careful", "avoid", "do not", "don’t",
    "never", "be sure", "make sure", 
    "you can", "you could", "optional",
    "can substitute", "you may", "if you prefer",
    "will thicken", "will change", "will form",
    "should look", "you'll see", "you will see",
    "as it", "it will", "it should"
]

ingredient_set = {}


def load_list_from_file(filepath: str) -> List[str]:
    """Load items (ingredients or tools) from a text file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        return []


def extract_ingredients(step: str, ingredient_data: List[Dict]) -> List[Dict]:
    """
    Return list of full ingredient dicts found in the step text.
    """
    step_lower = step.lower()
    results = []
    for ing in ingredient_data:
        ing_name_norm = normalize_ingredient(ing["name"])
        if ing_name_norm in step_lower:
            results.append(ing)
    return results


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
    temp_pattern = re.compile(r'(\d{2,3})\s*(?:°|degrees)\s*[cf]', re.IGNORECASE)
    temps = temp_pattern.findall(step)
    result = {}

    if temps:
        # If oven is mentioned or implied
        if re.search(r'oven', step.lower()):
            #print(temps[0])
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

def parse_step(step_number: int, step: str, ingredient_data: List[Dict], tools: List[str]) -> Dict:
    """Parse a single recipe step into a structured dict, including ingredient quantities."""
    step_ingredients = extract_ingredients(step, ingredient_data)  #full ingredient dicts
    step_tools = extract_tools(step, [tool for tool in tools])
    methods = extract_methods(step)
    time_info = extract_time(step)
    temp_info = extract_temperature(step, [ing["name"] for ing in step_ingredients])  # Use ingredient names for temperature function

    actions = extract_actions_rule_based(step, [ing["name"] for ing in step_ingredients], COOKING_VERBS, step_tools)

    return {
        "step_number": step_number,
        "description": step.strip(),
        "ingredients": step_ingredients,    # Now a list of dicts {qty, unit, name}
        "actions": actions,
        "time": time_info if time_info else {},
        "temperature": temp_info if temp_info else {},
    }


def extract_actions_rule_based(text, ingredients, cooking_verbs, tools_list):
    matcher = Matcher(nlp.vocab)
    doc = nlp(text)
    actions = []
    # print(matcher(doc))
    
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
    # name = re.sub(r'\b(shredded|chopped|diced|sliced|fresh|lean|ground)\b', '', name)
    # name = re.sub(r'or to taste|to taste', '', name)
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
            # print(ingredient + " " + str(score))

    # Sort by descending match strength
    matches.sort(key=lambda x: x[1], reverse=True)

    # Return only the ingredient names
    
    return [m[0] for m in matches]
    # text_lower = text.lower()
    # found = []
    
    # for ing in ingredient_set:
    #     ing_tokens = [t for t in re.findall(r"\b\w+\b", ing)]
    #     print(ing_tokens)
    #     match_count = sum(1 for t in ing_tokens if t in text_lower)
    #     if match_count / len(ing_tokens) >= 0.25:  # at least quarter of the tokens match
    #         found.append(ing)
    #     # pattern = [{"TEXT": {"FUZZY": {"IN": ing}}}]
    #     # matcher.add(text_lower, [pattern])
    # return found

def parse_step_main(step, tools, ingredients):
    parsed = parse_step(1, step, ingredients, tools)
    #print(json.dumps(parsed, indent=4))
    return parsed

def check_actionable(step: str) -> bool:
    """
    Classify a recipe step using spaCy, with fallback = actionable.
    """
    doc = nlp(step.strip())
    lower = step.lower().strip()

    # --- 1) Non-actionable pattern detection ---
    def contains(patterns):
        return any(p in lower for p in patterns)

    if contains(NON_ACTIONABLE_PATTERNS):
        return False

    # --- 2) Imperative verb detection ---
    # Identify true root token
    root = [t for t in doc if t.head == t][0]

    # Imperative = root verb + no subject
    if root.pos_ == "VERB":
        has_subject = any(child.dep_ in ("nsubj", "nsubjpass") for child in root.children)
        if not has_subject:
            return True

    # Starts with a verb (common recipe style)
    if doc[0].pos_ == "VERB":
        return True

    # Contains cooking-relevant verbs
    if any(token.lemma_ in COOKING_VERBS for token in doc):
        return True

    # --- 3) DEFAULT FALLBACK (more likely actionable) ---
    return True

def main():
    # if len(sys.argv) != 4:
    #     print("Usage: python parser.py ingredients.txt tools.txt 'Step sentence here'") #assumes scraper outputs an ingrediant list
    #     sys.exit(1)

    # ingredients_file = sys.argv[1]
    # tools_file = sys.argv[2]
    # step_sentence = sys.argv[3]

    with open("recipe.json", "r") as f:
        data = json.load(f)

    ingredients = [item["name"] for item in data["ingredients"]]
    # print("*********ingredients:", ingredients)

    # #ingredients = load_list_from_file(ingredients_file)
    tools_file = 'tools.txt'
    tools = load_list_from_file(tools_file)

    # parsed = parse_step(1, step_sentence, ingredients, tools)
    # print(json.dumps(parsed, indent=4))
    """
        I added more testing steps to test specific actionable/non-actionable cases. Decided to group all 
        non-actionable cases together, because I think that the most reasonable handling/storing of them
        is just to add them to the preivous step stored as plain-text. Ideal functionality would be for 
        the UI to check if the step has a warning or observation and output it after. I think that the
        warnings will gain minimal benefit from being parsed. 
        If we do decide to parse them we should store them as a normal step and add Actionable/non-actionable
        to all step tags. I'll then move non-actionable functionality into the parse_step.
    """
    testing_steps = {
        "Be careful not to overmix.",
        "You can substitute butter for oil.",
        "The sauce will thicken as it cools.",
        "Stir the mixture for 2 minutes.",
        "Bake at 350°F for 20 minutes.",
        "Once the dough rises, it should double in size.",
        "Chop the onions finely."
    }
    step = 'Lay 4 noodles side by side on the bottom of a 9x13-inch baking pan; top with a layer of prepared tomato-basil sauce, a layer of ground beef mixture, and a layer of cottage cheese mixture.'
    for step in testing_steps:
        actionable = check_actionable(step)
        if (actionable):
            parse_step_main(step, tools, ingredients)
        else:
            print(step + ": Non-actionable step, probably want to append to the previous step in a 'non-actionable' line\n")


if __name__ == "__main__":
    main()
