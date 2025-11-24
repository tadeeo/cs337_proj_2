import json
from parser_1 import load_list_from_file, parse_step

def load_tools():
    tools_file = 'src/tools.txt'
    tools = load_list_from_file(tools_file)
    return tools

def load_ingredients():
    with open("recipe.json", "r") as f:
        data = json.load(f)
    return data["ingredients"]   # Return list of dicts {qty, unit, name}

def load_steps():
    with open("recipe.json", "r") as f:
        data = json.load(f)
    steps = []
    for step in data["steps"]:
        for sub in step["substeps"]:
            steps.append({ "step_number": step["step_number"], "text": sub["text"] })
    return steps

def get_parsed_steps():
    steps = load_steps()
    tools = load_tools()
    ingredient_data = load_ingredients()
    parsed_steps = []
    step_counter = 1
    for step in steps:
        parsed_step = parse_step(step_counter, step['text'], ingredient_data, tools)
        parsed_step["step_number"] = step_counter
        parsed_steps.append(parsed_step)
        step_counter += 1
    return parsed_steps

def main():
    data = get_parsed_steps()
    with open("parsed_recipes.json", "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
