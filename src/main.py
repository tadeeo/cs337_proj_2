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
        output += "Notes: \n" + (s + "\n" for s in step["notes"])
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

import re

def handle_info_query(query: str, speech: bool) -> Tuple[bool, str]:
    handled = False
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
    while True:
        query = input("\n q -- ")
        query = query.strip().lower()
        if query.lower() in ['exit', 'quit']:
            slow_print("Goodbye! Happy cooking!")
            break
        
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