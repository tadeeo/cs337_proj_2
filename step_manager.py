import json


steps = []
curr_step = 0

def get_steps():
    global steps
    with open("parsed_recipes.json", "r") as f:
        steps = json.load(f)

def get_current_step():
    return steps[curr_step]["description"]

def set_next_step():
    global curr_step
    curr_step += 1

def set_prev_step():
    global curr_step
    curr_step -= 1

def get_temperature():
    temperatures = steps[curr_step]["temperature"]
    if len(temperatures) == 0:
        return "no temperatures to give"
    
    total = "set "
    for k,v in temperatures.items():
        total += k + " to " + v + ", "
    
    return total[:-2]

def get_ingredients(action):
    ingredients = steps[curr_step]["actions"][action]["ingredients"]
    return ", ".join(ingredients)

def get_action_index(action_verb):
    actions = steps[curr_step]["actions"]
    i = 0
    for action in actions:
        if action["verb"] == action_verb:
            return i
        i += 1

def main():
    get_steps()

    print(get_current_step())
    print(get_temperature())
    set_next_step()
    print(get_temperature())
    print(get_ingredients(0))
    set_next_step()
    print(get_action_index("cook"))

if __name__ == "__main__":
    main()
