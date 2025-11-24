import re
import sys
import time
import recipe_scraper
import recipe_parser
import step_manager
import json
from typing import Tuple

_DELAY_MULTIPLIER = 0.0 # for testing, set to 0.0 to skip delays

with open("recipe.json", "r", encoding="utf-8") as f:
    recipe_data = json.load(f)

with open("parsed_recipes.json", "r", encoding="utf-8") as f:
    parsed_recipe_data = json.load(f)

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

def handle_step_query(query, recipe_data, curr_idx, speech: bool) -> Tuple[bool, int, str]:
    """Handle step navigation queries (next, previous, first, repeat).

    Args:
        query (str): User query string.
        recipe_data: Unused here, kept for interface compatibility.
        curr_idx (int): Current step number (1-based).
        speech (bool): If True, return a string for TTS; else print.

    Returns:
        Tuple[bool, int, str]: (handled, new_curr_idx, output_for_speech).
    """
    steps = step_manager.get_steps()
    total_steps = steps[-1]["step_number"]
    handled = False
    output = ""

    q = query.lower().strip()

    next_step = re.compile(r"\b(next( step)?|forward|advance|go (to|onto) the next step)\b")
    prev_step = re.compile(r"\b(previous( step)?|prev|last step|go back|back( a step)?)\b")
    repeat_step = re.compile(r"\b(repeat( that)?|again|say (that|it) again|could you repeat)\b")
    first_step = re.compile(r"\b(first step|start( from the beginning)?|begin( at the start)?)\b")

    # NEXT
    if next_step.search(q):
        if curr_idx < total_steps:
            curr_idx += 1
        else:
            msg = "You’re already on the last step!"
            if speech:
                return True, curr_idx, msg
            slow_print(msg)
            return True, curr_idx, ""

    # PREVIOUS
    elif prev_step.search(q):
        if curr_idx > 1:
            curr_idx -= 1
        else:
            msg = "You’re already on the first step!"
            if speech:
                return True, curr_idx, msg
            slow_print(msg)
            return True, curr_idx, ""

    # FIRST
    elif first_step.search(q):
        curr_idx = 1

    # REPEAT: do not change curr_idx, just fall through and re-read current step
    elif repeat_step.search(q):
        pass
    
    else:
        return False, curr_idx, ""

    # Get all entries for this step_number
    step_entries = step_manager.get_current_step(steps, curr_idx)

    if speech:
        parts = [f"Step {curr_idx}:"]
        for entry in step_entries:
            parts.append(entry["description"])
        output = " ".join(parts)
    else:
        word_print("Step", curr_idx, ":")
        for entry in step_entries:
            word_print(entry["description"])
            tactical_pause()

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

    what_is_pat = re.compile(r"(what\s+is|what\s+does)\s+(.+?)(?:\s+mean)?[\?\s]*$")
    how_do_pat = re.compile(r"(how\s+(do|to)\s+(i\s+)?)(.+?)[\?\s]*$")
    how_much_pat = re.compile(r"(how\s+(much|many)\s+)(.+?)[\?\s]*$")

    m = what_is_pat.match(q)
    if m:
        term = m.group(2).strip()
        definition = culinary_dict.get(term)
        if definition:
            output = f"{term} means {definition}"
            handled = True
        elif term in cooking_tools:
            output = f"{term}: {cooking_tools[term]}"
            handled = True
        else:
            output = f"Sorry, I couldn't find a definition for {term}. Try searching online!"
            yt_url = make_youtube_search_url(term)
            output += f"\nYouTube search: {yt_url}"
            handled = True
        if speech:
            return handled, output
        else:
            word_print(output)
            return handled, output

    m = how_do_pat.match(q)
    if m:
        procedure = m.group(4).strip()
        definition = culinary_dict.get(procedure)
        if definition:
            output = f"{procedure} means {definition}"
            handled = True
        elif procedure in cooking_tools:
            output = f"{procedure}: {cooking_tools[procedure]}"
            handled = True
        else:
            output = f"Sorry, I couldn't find info for {procedure}. Try searching online!"
            yt_url = make_youtube_search_url(procedure)
            output += f"\nYouTube search: {yt_url}"
            handled = True
        if speech:
            return handled, output
        else:
            word_print(output)
            return handled, output

    # how-much / how-many lookup
    m = how_much_pat.match(q)
    if m:
        target = m.group(3).strip().lower()
        found = None
        for step in parsed_recipe_data:
            for ing in step.get("ingredients", []):
                if target in ing.get("name", "").lower():
                    qty = ing.get("qty", "").strip()
                    unit = ing.get("unit", "").strip()
                    if qty or unit:
                        found = f"{qty} {unit}".strip()
                        output = f"You typically need {found} of {ing['name']}"
                        handled = True
                        break
            if handled:
                break
        if not handled:
            output = f"Sorry, I don't know how much {target} you need."
            handled = True
        if speech:
            return handled, output
        else:
            word_print(output)
            return handled, output

    # Final fallback if nothing matched
    if not handled:
        output = "Sorry, I couldn't find an answer. Try searching online!"
        yt_url = make_youtube_search_url(q)
        output += f"\nYouTube search: {yt_url}"
        word_print(output)
        handled = True
    return handled, output

def handle_temp_query(query):
    handled = False
    q = query.lower().strip()
    temp_pat = re.compile(
        r"\b(temperature\??|what('s| is)? the temperature|what temperature|set temperature)\b"
    )

    if temp_pat.search(q):
        temperature_info = step_manager.get_temperature()
        if temperature_info and temperature_info.lower() != "no temperatures to give":
            word_print("The temperature information is as follows:")
            word_print(temperature_info)
        else:
            word_print("Sorry, there is no temperature information for this step.")
        handled = True
    return handled

def query_handler():
    slow_print(" Great!")
    slow_print(" Now, we will begin navigating the recipe! At any point during the experience, you can type 'exit' to quit.")
    slow_print(" Whenever you're ready, ask 'What is the first step?' to begin.")
    idx = 1
    while True:
        query = input("\n q -- ").strip().lower()
        if query in ['exit', 'quit']:
            slow_print("Goodbye! Happy cooking!")
            break

        handled, idx, _ = handle_step_query(query, recipe_data, idx, False)
        if handled:
            continue
        handled = handle_temp_query(query)
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