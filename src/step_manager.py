import json


steps = []
curr_step = 1

def get_steps():
    """
    Load all parsed recipe steps from 'parsed_recipes.json'.

    Returns:
        list: List of parsed step dictionaries for the recipe.
    """
    global steps
    with open("src/parsed_recipes.json", "r") as f:
        steps = json.load(f)
    return steps

def get_current_step(steps, curr_step):
    """
    Return all step dictionaries for the given step number.

    Args:
        steps (list): List of step dictionaries.
        curr_step (int): The current step number.

    Returns:
        list: List of steps matching the given step number.
    """
    return steps[curr_step-1]

def set_next_step(steps, curr_step):
    """
    Increment the current step number.

    Args:
        steps (list): List of step dictionaries (not used in function).
        curr_step (int): The current step number.

    Returns:
        int: The next step number.
    """
    curr_step += 1
    return curr_step

def set_prev_step():
    """
    Decrement the global current step number.

    Returns:
        None
    """
    global curr_step
    curr_step -= 1

def get_temperature():
    """
    Get all temperature settings for the current step.

    Returns:
        str: Formatted temperatures, or message if not present.
    """
    temperatures = []
    i = 0
    while steps[i]["step_number"] == curr_step:
        temperatures.append(steps[i]["temperature"])
        i += 1
        
    if len(temperatures) == 0:
        return "no temperatures to give"
    
    total = "set "
    for temp in temperatures:
        for k, v in temp.items():
            total += k + " to " + v + ", "
    
    return total[:-2]

def get_ingredients(i, action):
    """
    Get ingredient names for a specific action in a step.

    Args:
        i (int): Step index.
        action (int): Action index.

    Returns:
        str: Comma-separated ingredient names.
    """
    ingredients = steps[i]["actions"][action]["ingredients"]
    return ", ".join(ingredients)

def get_action_index(action_verb):
    """
    Find the step and action index for an action with a given verb.

    Args:
        action_verb (str): Action verb to search for.

    Returns:
        tuple: Indices (step_index, action_index) where action is found.
    """
    j = 0
    for step in steps:
        actions = step["actions"]
        i = 0
        for action in actions:
            if action["verb"] == action_verb:
                return (j, i)
            i += 1
        j += 1

def main():
    steps = get_steps()
    # print(steps)
    # print(get_current_step(steps, 1))
    # print(get_temperature())
    # set_next_step()
    # print(get_temperature())
    # print(get_ingredients(1,0))
    # set_next_step()
    # print(get_action_index("cook"))

if __name__ == "__main__":
    main()
