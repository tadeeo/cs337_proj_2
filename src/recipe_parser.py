import json
from parser_1 import load_list_from_file, parse_step_main

def load_tools():
    tools_file = 'tools.txt'
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
    #sub_steps = [{"substeps": item["substeps"], "step_number": step for item in data["steps"]]
    for sub in data["steps"]:
        for i in range(len(sub["substeps"])):
            text.append({ "step_number": sub["step_number"], "substep_number": sub["substeps"][i]["sub_number"], "text": sub["substeps"][i]["text"] })
    
    print(text)        
    return text

def get_parsed_steps():
    steps = load_steps()
    tools = load_tools()
    ingredients = load_ingredients()
    parsed_steps = []

    for step in steps:
        parsed_step = parse_step_main(step['text'], tools, ingredients)
        parsed_step["step_number"] = step["step_number"]
        parsed_step["substep_number"] = step["substep_number"]
        parsed_step = parse_step_main(step['text'], tools, ingredients)
        parsed_steps.append(parsed_step)
    return parsed_steps

def main():
    data = get_parsed_steps()
    with open("parsed_recipes.json", "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
