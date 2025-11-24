import re
import time
import recipe_scraper
import recipe_parser
import step_manager
import json
from typing import Tuple

_DELAY_MULTIPLIER = 0.0 # for testing, set to 0.0 to skip delays

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

# ------------ Helper for handle_vague_query: extract a good replacement phrase ------------
def get_replacement_phrase(step):
    """Return the most relevant description for vague noun replacement."""
    # Prefer action + ingredient ("pour the batter")
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

# ------------ Replace vague terms ------------
def replace_vague_terms(q: str, phrase: str, vague_terms: str):
    # Whole-word replace only
    for vt in vague_terms:
        q = re.sub(rf"\b{vt}\b", phrase, q, flags=re.I)
    return q

def handle_vague_query(query, curr_idx, speech: bool) -> Tuple[bool, str]:
    """Handles vague queries by replacing vague nouns ('it', 'that', etc.) with
       the most relevant action or ingredient from the current step, then
       forwarding to handle_info_query(). Returns (handled, output)."""

    steps = step_manager.get_steps()
    step = step_manager.get_current_step(steps, curr_idx)

    # --- Patterns already defined ---
    what_is_pat = re.compile(r"(what\s+is|what\s+does)\s+(.+?)(?:\s+mean)?[\?\s]*$", re.I)
    how_do_pat = re.compile(r"(how\s+(do|to)\s+(i\s+)?)(.+?)[\?\s]*$", re.I)
    how_much_pat = re.compile(r"(how\s+(much|many)\s+)(.+?)[\?\s]*$", re.I)

    # --- Vague terms ---
    vague_terms = ["it", "that", "this", "them"]

    replacement_phrase = get_replacement_phrase(step)

    # Normalize for regex matching
    lower_query = query.lower()

    # # Detect whether any vague pronoun is present
    # if not any(vt in lower_query.split() for vt in vague_terms):
    #     return False, ""   # Not vague — not handled here

    rewritten_query = replace_vague_terms(query, replacement_phrase, vague_terms)

    # Change to a fall back phrase instead
    # ------------ Must match one of the info-query patterns ------------
    # if not (what_is_pat.match(rewritten_query) or
    #         how_do_pat.match(rewritten_query) or
    #         how_much_pat.match(rewritten_query)):
    #     # Vague but not an info query → handled but no info
    #     return True, f"I rewrote your question as: '{rewritten_query}', " \
    #                  "but it doesn’t look like an info question."

    # ------------ Delegate to info handler ------------
    handled, output = handle_info_query(rewritten_query, speech)
    return handled, output

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
    subs = {}
    try:
        with open("src/substitutions.txt", "r") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                key, vals = line.split(":", 1)
                key = key.strip().lower()
                vals = [v.strip() for v in vals.split(",") if v.strip()]
                subs[key] = vals
    except Exception as e:
        return True, f"Error reading substitutions file: {e}"



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

    step = step_manager.get_current_step(steps, curr_idx)
    if speech:
        output += "Step " + str(step['step_number']) + ": " + str(step['description'] + " ")
        print(output)
    else:
        print(step)
        word_print("Step", step['step_number'], ":", step['description'])
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

def handle_info_query(query: str, speech: bool) -> Tuple[bool, str]:
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

    # Can't find lookup
    if not handled:
          yt_query = q.replace(" ", "+")
          youtube_url = f"https://www.youtube.com/results?search_query={yt_query}"
          word_print("For more information, feel free to try this YouTube search:")
          word_print(youtube_url)
          handled = True

    # how-much / how-many lookup
    if not handled:
        m = how_much_pat.match(q)
        if m:
            target = m.group(3).strip()
            amount = parsed_recipe_data["ingredients"]
            if amount:
                word_print("You typically need", amount, "of", target)
            else:
                word_print("Sorry, I don't know how much", target, "you need.")
            handled = True
    return handled, output

def handle_temp_query(query):
    handled = False
    q = query.lower().strip()
    temp_pat = re.compile(r"(what\s+is\s+the\s+temperature\s+for|set\s+the\s+temperature\s+to)[\?\s]*$")

    m = temp_pat.match(q)
    if m:
        temperature_info = step_manager.get_temperature()
        word_print("The temperature information is as follows:")
        word_print(temperature_info)
        handled = True
    return handled

def query_handler():
    slow_print(" Great!")
    slow_print(" Now, we will begin navigating the recipe! At any point during the experience, you can type 'exit' to quit.")
    slow_print(" Whenever you're ready, ask 'What is the first step?' to begin.")
    idx = 1
    handled = False
    while True:
        query = input("\n q -- ")
        query = query.strip().lower()
        if query.lower() in ['exit', 'quit']:
            slow_print("Goodbye! Happy cooking!")
            break
        
        if not handled:
            handled, idx = handle_vague_query(query, idx, False)
        
        if not handled:
            handled, idx = handle_substitution_query(query, idx, False)

        handled, idx, _ = handle_step_query(query, recipe_data, idx, False)
        if handled:
            continue
        handled, _ = handle_info_query(query, False)
        if handled:
            continue
        slow_print("Sorry, I didn't understand that. Please try again.")
    
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