import requests
from bs4 import BeautifulSoup

url = "https://whatscookingamerica.net/glossary/"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

culinary_terms = {}

# Loop over each .col-sm-12 block (each dictionary entry)
for entry in soup.select("div.col-sm-12"):
    # Get the term
    name_tag = entry.select_one("strong[itemprop='name']")
    term = name_tag.get_text(strip=True) if name_tag else None
    
    # Get the definition
    desc_tag = entry.select_one("span[itemprop='description'] > p")
    definition = desc_tag.get_text(" ", strip=True) if desc_tag else None
    
    # Only add if both are found and definition is not just a hyphen
    if term and definition and definition != "-":
        # Optionally: remove anything after "History:"
        if "History:" in definition:
            definition = definition.split("History:")[0].strip()
        culinary_terms[term] = definition

# Print or use the dictionary
for term, definition in list(culinary_terms.items())[:10]:  # show first 10
    print(f"{term}: {definition}\n")

# Optionally, save as JSON dictionary
import json
with open("culinary_dictionary.json", "w", encoding="utf-8") as f:
    json.dump(culinary_terms, f, indent=2, ensure_ascii=False)
