python3 src/main.py
## Installing Requirements


## Running
To run `main.py`, simply run `python3 src/main.py` (this is where user iterpreter lies).

### Lasagna Recipe
https://www.allrecipes.com/recipe/218091/classic-and-simple-meat-lasagna/

#### Queries
- “Show me the ingredients list.”
- "Display the recipe"
- “Go back one step.”
- “Go to the next step.”
- “Repeat please.”
- “Take me to the first step.”
- “What’s next?”
- “What was that again?”

**At step 2:**
- “How much salt do I need?”
- “What temperature should the oven be?”
- “How long do I boil it?”
- “When is it done?”

**At step 4:**
- "What can I use instead of pepper?"
- “What is a skillet?”

**At step 5:**
- "How do I mix?"
- "How do I do that?"
- "How many eggs do I need?"
- "How much of that do I need?"

### Orange Cake Recipe
https://www.allrecipes.com/recipe/261757/orange-cake-with-semolina-and-almonds/


## Files
### main.py
The main scripter file that handles user queries. This calls other functions to get info regarding the recipe, and handles logistics for current step.

### recipe_scraper.py
Scraper file- scrapes the given recipe and seperates into basic steps/ingredients, saves this into `recipe.json`.

### recipe_parser.py
Uses `recipe.json` to parse each step and gain info regarding step action, ingredients, temperature to cook at, tools, etc. `parser_1.py` is a helper file.

### step_manager.py
Returns helper information regarding queries for current step.

### speech_to_text.py
Handles logic for adding speech to text to interpret user inputs.

### culinary_term_scraper.py, temp_tool_extractor.py
Extracts info that would be helpful for parser/query functions.
Helper json/txt files:
`common_cooking_tools.txt`, `culinary_dictionary.json`, `tools.txt`