import json
from parser_1 import load_list_from_file, parse_step_main

def load_tools():
    tools_file = 'src/tools.txt'
    tools = load_list_from_file(tools_file)
    return tools

def load_ingredients():
    with open("recipe.json", "r") as f:
        data = json.load(f)

    ingredients = [item["name"] for item in data["ingredients"]]
    return ingredients

def load_steps():
    with open("recipe.json", "r") as f:
        data = json.load(f)

    text = []
    sub_steps = [item["substeps"] for item in data["steps"]]
    for sub in sub_steps:
        text.append(sub[0]["text"])
    return text

def get_parsed_steps():
    steps = load_steps()
    tools = load_tools()
    ingredients = load_ingredients()
    parsed_steps = []

    for step in steps:
        parsed_steps.append(parse_step_main(step, tools, ingredients))
    return parsed_steps

def main():
    data = get_parsed_steps()
    with open("parsed_recipes.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
