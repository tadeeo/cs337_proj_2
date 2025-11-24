import json
import requests
from bs4 import BeautifulSoup

URL = "https://www.allrecipes.com/article/common-ingredient-substitutions/"

def scrape_ingredient_substitutions():
    resp = requests.get(URL)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Grab the main substitutions table
    table = soup.select_one("table.mntl-sc-block-universal-table__table")
    if not table:
        raise RuntimeError("Could not find substitutions table on page")

    tbody = table.find("tbody") or table

    subs = []
    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue

        ingredient = tds[0].get_text(" ", strip=True)
        amount     = tds[1].get_text(" ", strip=True)
        substitution = tds[2].get_text(" ", strip=True)

        # skip header row or junk
        if ingredient.lower() == "ingredient":
            continue

        subs.append({
            "ingredient": ingredient,
            "qty": amount,
            "substitution": substitution,
        })

    return subs


if __name__ == "__main__":
    data = scrape_ingredient_substitutions()
    with open("ingredient_substitutions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
