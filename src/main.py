import re
import time
import recipe_scraper
import recipe_parser
import step_manager
import json
from typing import Tuple

_DELAY_MULTIPLIER = 0.0 # for testing, set to 0.0 to skip delays

subs = {}
with open("src/ingredient_substitutions.json", "r") as f:
    data = json.load(f)

    # Expecting a list of objects
    for entry in data:
        ingredient = entry.get("ingredient")
        substitution = entry.get("substitution")

        if not ingredient or not substitution:
            continue  # skip incomplete rows

        subs[ingredient.lower()] = substitution

with open("src/recipe.json", "r", encoding="utf-8") as f:
    recipe_data = json.load(f)

# with open("parsed_recipes.json", "r", encoding="utf-8") as f:
#     parsed_recipe_data = json.load(f)

with open("src/culinary_dictionary.json", "r", encoding="utf-8") as f:
    culinary_dict = json.load(f)

def load_cooking_tools():
    # returns a dict: {"Hand whisk": "...", "...": "..."}
    tools = {}
    with open("src/common_cooking_tools.txt", "r", encoding="utf-8") as f:
        for line in f:
            if ':' in line:
                name, desc = line.split(':', 1)
                tools[name.strip().lower()] = desc.strip()
    return tools

cooking_tools = load_cooking_tools()

def slow_print(*args, delay=0.025):
    text = ''.join(str(arg) for arg in args)
    for char in text:
        print(char, end='', flush=True)
        time.sleep(_DELAY_MULTIPLIER*delay)
    tactical_pause()
    print()  # Move to the next line after printing

def word_print(*args, delay=0.15):
    text = ' '.join(str(arg) for arg in args)
    words = text.split()
    for word in words:
        print(word, end=' ', flush=True)
        time.sleep(_DELAY_MULTIPLIER*delay)
    print() 

def tactical_pause(seconds = 0.35):
    time.sleep(_DELAY_MULTIPLIER*seconds)

def scrape_and_parse(url: str):
    recipe_scraper.main(url)
    recipe_parser.main()
    step_manager.main()
    slow_print("Scraping and parsing complete!")

def make_google_search_url(q):
    g_query = q.replace(" ", "+")
    return f"https://www.google.com/search?q={g_query}"

def make_youtube_search_url(q):
    yt_query = q.replace(" ", "+")
    return f"https://www.youtube.com/results?search_query={yt_query}"

def startup_base():
    slow_print("What recipe would you like to cook today?")
    url = input("\nEnter recipe url: ")
    slow_print("\nGreat! Let's scrape and parse this delicious recipe!")
    tactical_pause()
    scrape_and_parse(url)
    tactical_pause(3)
    slow_print("Let's see what we have!")
    word_print("\nRecipe Details:\n", delay=0.3)
    word_print("Title:", recipe_data["title"],), tactical_pause()
    word_print("Prep time:", recipe_data["prep_time"]), tactical_pause()
    word_print("Cook time:", recipe_data["cook_time"]), tactical_pause()
    word_print("Additional time:", recipe_data["additional_time"]), tactical_pause()
    word_print("Total time:", recipe_data["total_time"]), tactical_pause()
    word_print("Yield:", recipe_data["yield"], " servings"), tactical_pause()
    word_print("\nIngredients:")
    
    for ingredient in recipe_data["ingredients"]:
        slow_print("- ", ingredient["qty"]," ", ingredient["unit"]," ", ingredient["name"], delay=0.02), tactical_pause()
    tactical_pause(.5)
    
    print("\n\n")
    slow_print(" And the steps are as follows:\n")
    
    for step in recipe_data["steps"]:
        print()
        word_print("Step ", step["step_number"], ": ", step["text"], delay=0.15), tactical_pause(1.5)

# ------------------------------------------------------------
# Helper: choose best phrase to replace "it / that / this / them"
# ------------------------------------------------------------
def get_replacement_phrase(step):
    """Return the most relevant description for vague-noun replacement."""

    # Prefer an ingredient-targeting phrase
    if step.get("actions"):
        action = step["actions"][0]
        verb = action.get("verb")
        ingredients = action.get("ingredients", [])

        if verb and ingredients:
            ing_phrase = ", ".join(ingredients)
            return f"{verb} the {ing_phrase}"
        if verb:
            return verb

    # Fallback to step description
    return step.get("description", "the current step")


# ------------------------------------------------------------
# Replacement of vague pronouns
# ------------------------------------------------------------
def replace_vague_terms(q: str, phrase: str, vague_terms):
    for vt in vague_terms:
        q = re.sub(rf"\b{vt}\b", phrase, q, flags=re.I)
    return q

def contains_vague_term(query):
    vague_terms = ["it", "that", "this", "them"]
    for vt in vague_terms:
        if re.search(rf"\b{vt}\b", query, flags=re.I):
            return True
    return False

# ------------------------------------------------------------
# Extract primary ingredient of current step
# ------------------------------------------------------------
def get_primary_ingredient(step):
    if not step or not isinstance(step, dict):
        return None
    if step.get("actions"):
        ingredients = step["actions"][0].get("ingredients", [])
        return ingredients[0] if ingredients else None
    return None

# ------------------------------------------------------------
# Extract time / temperature if present
# ------------------------------------------------------------
def get_step_time_phrase(step):
    t = step.get("time", {})
    if not t:
        return None

    if "duration" in t:
        return t["duration"]

    if "min" in t and "max" in t:
        return f"{t['min']} to {t['max']} minutes"

    if "min" in t:
        return f"{t['min']} minutes"

    return None


def get_step_temp_phrase(step):
    temp = step.get("temperature", {})
    if not temp:
        return None

    if "fahrenheit" in temp:
        return f"{temp['fahrenheit']}°F"
    if "celsius" in temp:
        return f"{temp['celsius']}°C"

    return None

# ------------------------------------------------------------
# Main vague query handler
# ------------------------------------------------------------
def handle_vague_query(query, curr_idx, speech: bool) -> Tuple[bool, str]:

    steps = step_manager.get_steps()
    step = step_manager.get_current_step(steps, curr_idx)

    vague_terms = ["it", "that", "this", "them"]
    replacement_phrase = get_replacement_phrase(step)
    lower_query = query.lower()

    # --------------------------------------------------------
    # Specific disambiguation based on question type
    # --------------------------------------------------------

    # --- Case 1: "how much of that / how much of it" → quantity inquiry
    how_much_of_pat = re.compile(r"how\s+much\s+of\s+(it|that|this|them)", re.I)
    if how_much_of_pat.search(query):
        ingredient = get_primary_ingredient(step)
        if not ingredient:
            return True, "I'm not sure which ingredient you're referring to."

        qty = find_ingredient_quantity(ingredient, steps)
        if qty:
            return True, f"You need {qty} of {ingredient}."
        else:
            return True, f"I couldn't find the quantity for {ingredient}."

    # --- Case 2: "how long do I bake it / how long should I cook that"
    how_long_pat = re.compile(r"how\s+long.*\b(it|that|this|them)\b", re.I)
    if how_long_pat.search(query):
        t = get_step_time_phrase(step)
        if t:
            return True, f"You should cook it for {t}."
        return True, "This step doesn't specify a cooking time."

    # --- Case 3: "what can I use instead of it/that" → ingredient substitution
    substitution_pat = re.compile(r"(use|substitute|instead of)\s+(it|that|this|them)", re.I)
    if substitution_pat.search(query):
        ingredient = get_primary_ingredient(step)
        if not ingredient:
            return True, "I'm not sure which ingredient you're referring to."
        # Let your existing substitution handler take over
        return handle_substitution_query(f"what can I use instead of {ingredient}", curr_idx, speech)

    # --------------------------------------------------------
    # Generic ambiguous replacement + forward to info handler
    # --------------------------------------------------------

    rewritten_query = replace_vague_terms(query, replacement_phrase, vague_terms)

    handled, output = handle_info_query(rewritten_query, speech)
    return handled, output

# ------------------------------------------------------------
# Utility: find ingredient quantity from steps
# ------------------------------------------------------------
def find_ingredient_quantity(ingredient, steps): #TODO Pull from original ingredient list
    """
    Search ingredients across all steps to find a matching quantity entry.
    You can customize this depending on how you store quantities.
    """

    ingredient = ingredient.lower()

    for step in steps:
        if step.get("actions"):
            for act in step["actions"]:
                if "ingredients" not in act:
                    continue

                # Your ingredients may have associated quantity metadata elsewhere.
                # If quantity is stored in the ingredient list as a dict:
                #   { "name": "sugar", "qty": "1 cup" }
                # then use this version:
                ing_list = act["ingredients"]

                for ing in ing_list:
                    if isinstance(ing, dict):
                        name = ing.get("name", "").lower()
                        qty = ing.get("qty")
                        if name == ingredient and qty:
                            return qty

                    elif isinstance(ing, str):
                        # If ingredient quantities are not stored in steps,
                        # they may come from a recipe ingredient list.
                        # You can plug that in here:
                        continue

    return None

def handle_substitution_query(query: str, curr_idx: int, speech: bool) -> Tuple[bool, str]:
    """
    Detects when the user asks for a substitution (e.g., "What can I use instead of butter?")
    Extracts the ingredient, looks up a substitution in substitutions.txt, and returns an answer.

    Returns (handled: bool, output: str)
    """

    # ---------------- PATTERNS ----------------
    sub_patterns = [
        re.compile(r"substitute\s+for\s+(.+)", re.I),
        re.compile(r"use\s+instead\s+of\s+(.+)", re.I),
        re.compile(r"replacement\s+for\s+(.+)", re.I),
        re.compile(r"what\s+can\s+i\s+use\s+for\s+(.+)", re.I),
        re.compile(r"what\s+can\s+i\s+use\s+instead\s+of\s+(.+)", re.I),
        re.compile(r"what\s+is\s+a\s+good\s+substitute\s+for\s+(.+)", re.I)
    ]

    match = None
    for pat in sub_patterns:
        match = pat.search(query)
        if match:
            break

    if not match:
        return False, ""   # Not a substitution question

    # -------------------------------------------------
    #     EXTRACT RAW INGREDIENT TERM FROM QUERY
    # -------------------------------------------------
    raw_ing = match.group(1).strip().lower()

    # Normalize plurals or trailing punctuation
    raw_ing = re.sub(r"[?.!]", "", raw_ing)
    raw_ing = raw_ing.rstrip('s') if raw_ing.endswith('s') else raw_ing

    # -------------------------------------------------
    #          COLLECT INGREDIENTS FOR MATCHING
    # -------------------------------------------------
    steps = step_manager.get_steps()
    current = step_manager.get_current_step(steps, curr_idx)

    def collect_ingredients(step):
        ings = []
        for action in step.get("actions", []):
            ings.extend(action.get("ingredients", []))
        return [i.lower() for i in ings]

    # Start with current step ingredients (most relevant)
    candidate_ings = collect_ingredients(current)

    # If not found, scan entire recipe as fallback
    if raw_ing not in candidate_ings:
        for st in steps:
            step_ings = collect_ingredients(st)
            candidate_ings.extend(step_ings)

    # Try fuzzy-ish matching: ingredient contains the query word
    matched_ing = None
    for ing in candidate_ings:
        if raw_ing in ing:
            matched_ing = ing
            break

    if not matched_ing:
        return True, f"I couldn't find the ingredient '{raw_ing}' in the recipe."

    # -------------------------------------------------
    #             LOAD SUBSTITUTIONS.TXT
    # -------------------------------------------------
    # Handled globally

    # -------------------------------------------------
    #             FIND SUBSTITUTIONS
    # -------------------------------------------------
    # direct match
    if matched_ing in subs:
        sub_list = subs[matched_ing]
    # plural/singular check
    elif matched_ing.rstrip("s") in subs:
        sub_list = subs[matched_ing.rstrip("s")]
    else:
        return True, f"I couldn't find any substitutions for {matched_ing}."

    # Format for output
    if len(sub_list) == 1:
        sub_text = sub_list[0]
    else:
        sub_text = ", ".join(sub_list[:-1]) + f", or {sub_list[-1]}"

    # -------------------------------------------------
    #           RETURN FORMATTED SUBSTITUTION
    # -------------------------------------------------
    response = f"You can substitute **{matched_ing}** with: {sub_text}."
    return True, response

def handle_step_query(query, recipe_data, curr_idx, speech: bool) -> Tuple[bool, int, str]:
    """ Handles step navigation queries.
        Returns (handled: bool, new_curr_idx: int)"""
    steps = step_manager.get_steps()
    total_steps = steps[len(steps)-1]["step_number"]
    handled = False
    output = "Output example "
    
    q = query.lower().strip()

    # regex to id step instruc
    next_step = re.compile(r"\b(next|forward|advance)\b")
    prev_step = re.compile(r"\b(previous|prev|last|back|before)\b")
    repeat_step = re.compile(r"\b(repeat|again|say (that|it) again)\b")
    first_step = re.compile(r"\b(first step|start|begin)\b")
    
    if next_step.search(q):
        if curr_idx < total_steps:
            curr_idx += 1
        else:
            if speech:
                output = "You’re already on the last step!"
                return True, curr_idx, output
            else:
                slow_print("You’re already on the last step!")
                return True, curr_idx, output
            
    elif prev_step.search(q):
        if curr_idx > 1:
            curr_idx -= 1
        else:
            if speech:
                output = "You’re already on the first step!"
                return True, curr_idx, output
            else:
                slow_print("You’re already on the first step!")
                return True, curr_idx, output

    elif first_step.search(q):
        curr_idx = 1

    elif repeat_step.search(q):
        curr_idx = curr_idx
    
    else:
        return False, curr_idx, ""

    step = step_manager.get_current_step(steps, curr_idx)
    if speech:
        output += "Step " + str(step['step_number']) + ": " + str(step['description'] + " ")
        for note in step["notes"]:
            output += note + "\n"
        print(output)
    else:
        print(step)
        word_print("Step", step['step_number'], ":", step['description'])
        word_print("Notes: \n" + print(s + "\n") for s in step["notes"])
    handled = True
    return handled, curr_idx, output

def handle_can_i_query(query):
    handled = False
    q = query.lower().strip()
    title = recipe_data["title"].lower().strip()
    goog_title = title.replace(" ", "+")
    can_i_pat = re.compile(r"can\s+i\s+(.+?)[\?\s]*$")

    m = can_i_pat.match(q)
    if m:
        action = m.group(1).strip()
        # check culinary dictionary
        definition = culinary_dict.get(action)
        if definition:
            word_print("Yes, you can", action + ":", definition)
            handled = True
        else:
            word_print("Sorry, I couldn't find information about", action)
            handled = True
    return handled

def handle_info_query(query: str, speech: bool, curr_idx) -> Tuple[bool, str]:
    handled = False
    output = ""
    q = query.lower().strip()

    # what is / what does ... mean
    what_is_pat = re.compile(r"(what\s+is|what\s+does)\s+(.+?)(?:\s+mean)?[\?\s]*$")
    # how do / how to ...
    how_do_pat = re.compile(r"(how\s+(do|to)\s+(i\s+)?)(.+?)[\?\s]*$")
    # how much / how many ...
    how_much_pat = re.compile(r"(how\s+(much|many)\s+)(.+?)[\?\s]*$")

    # what-is lookup
    m = what_is_pat.match(q)
    if m:
        term = m.group(2).strip()
        definition = culinary_dict.get(term)
        if speech: # Could also move speech check inside the ifs
            if definition:
                output = term + "means " + definition
                return True, output
            #  check cooking tools
            elif term in cooking_tools:
                output = term + " " + cooking_tools[term]
                return True, output
            else:
                output = "Sorry, I couldn't find a definition for " + term
                return True, output
        else:
            if definition:
                word_print(term, "means:", definition)
                handled = True
            #  check cooking tools
            elif term in cooking_tools:
                word_print(term, ":", cooking_tools[term])
                handled = True
            else:
                word_print("Sorry, I couldn't find a definition for", term)
                handled = True
    
    
    # how-to lookup
    m = how_do_pat.match(q)
    if m:
        procedure = m.group(4).strip()
        definition = culinary_dict.get(procedure)
        if speech: # I mimicked the existing code here, but am unsure of the purpose? Why would procedure ever be in cooking tools? Also, you're youtube searching no matter what?
            if definition:
                output = procedure + "means " + definition
                return True, output
            # check tools
            elif procedure in cooking_tools:
                output = procedure + " " + cooking_tools[procedure]
                return True, output
        else:
            if definition:
                word_print(procedure, "means:", definition)
            # check tools
            elif procedure in cooking_tools:
                word_print(procedure, ":", cooking_tools[procedure])

    # how-much / how-many lookup
    if not handled:
        m = how_much_pat.match(q)
        #print('how much: ' + m)
        if m:
            target = m.group(3).strip()
            steps = step_manager.get_steps()
            amount = step_manager.get_current_step(steps, curr_idx)
            known = False
            if amount:
                for ing in amount["ingredients"]:
                    if ing["name"] == target:
                        word_print("You typically need", ing["qty"], ing["unit"], "of", target)
                        known = True
                if not known:
                    word_print("Sorry, I don't know how much", target, "you need.")
            else:
                word_print("Sorry, I don't know how much", target, "you need.")
            handled = True

    # Can't find lookup
    if not handled:
          yt_query = q.replace(" ", "+")
          youtube_url = f"https://www.youtube.com/results?search_query={yt_query}"
          word_print("For more information, feel free to try this YouTube search:")
          word_print(youtube_url)
          handled = True
    
    return handled, output

def handle_temp_query(query):
    handled = False
    q = query.lower().strip()
    temp_pat = re.compile(r"what\s+is\s+the\s+temperature\s+for.*$")

    m = temp_pat.match(q)
    temperature_info = ""
    if m:
        temperature_info = step_manager.get_temperature()
        word_print("The temperature information is as follows:")
        word_print(temperature_info)
        handled = True
    return handled, "The temperature is " + temperature_info

def query_handler():
    slow_print(" Great!")
    slow_print(" Now, we will begin navigating the recipe! At any point during the experience, you can type 'exit' to quit.")
    slow_print(" Whenever you're ready, ask 'What is the first step?' to begin.")
    idx = 1
    while True:
        handled = False
        query = input("\n q -- ")
        query = query.strip().lower()
        if query.lower() in ['exit', 'quit']:
            slow_print("Goodbye! Happy cooking!")
            break
        
        if not handled:
            if (contains_vague_term(query)):
                handled, output = handle_vague_query(query, idx, True)
                print("vague: " + output + ":")

        if not handled:
            handled, output = handle_temp_query(query)
            print(output)
        
        if not handled:
            handled, output = handle_substitution_query(query, idx, True)
            print("sub: " + output + ":")

        if not handled:
            handled, idx, output = handle_step_query(query, recipe_data, idx, True)
            print("step: " + output + ":")

        if not handled:
            handled, output = handle_info_query(query, True, idx)
            print("info: " + output + ":")
        
        if not handled:
            slow_print("Sorry, I didn't understand that. Please try again.")

        slow_print(output)
    
def main():
    
    startup_base()
    slow_print("Would you like to interact with this recipe?")
    yes_or_no = input(" y/n : ")
    yes_or_no = yes_or_no.strip()
    if yes_or_no.lower() in ['y', 'yes', 'sure', 'yeah']:
        query_handler()
    elif yes_or_no.lower() in ['n', 'no', 'nah', 'nope']:
        slow_print("Alright! Enjoy your cooking!")
    else:
        print("Invalid input. Please enter 'y' or 'n'.")

if __name__ == "__main__":
    main()