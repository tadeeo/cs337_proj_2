import json


steps = []
curr_step = 1

def get_steps():
    global steps
    with open("parsed_recipes.json", "r") as f:
        steps = json.load(f)
    return steps

def get_current_step(steps, curr_step):
    curr = []
    for step in steps:
        if step["step_number"] == curr_step:
            curr.append(step)
        else:
            continue
    return curr

def set_next_step(steps, curr_step):
    curr_step
    curr_step += 1
    return curr_step

def set_prev_step():
    global curr_step
    curr_step -= 1

def get_temperature():
    temperatures = []
    i = 0
    while steps[i]["step_number"] == curr_step:
        temperatures.append(steps[i]["temperature"])
        i += 1
        
    if len(temperatures) == 0:
        return "no temperatures to give"
    
    total = "set "
    for temp in temperatures:
        for k,v in temp.items():
            total += k + " to " + v + ", "
    
    return total[:-2]

def get_ingredients(i, action):
    ingredients = steps[i]["actions"][action]["ingredients"]
    return ", ".join(ingredients)

def get_action_index(action_verb):
    j = 0
    for step in steps:
        actions = step["actions"]
        i = 0
        for action in actions:
            if action["verb"] == action_verb:
                return (j,i)
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
