# recipe_scraper.py
import sys, re, json
import requests
from bs4 import BeautifulSoup

def fetch_soup(url: str) -> BeautifulSoup:
    """
    Fetch HTML and return a BeautifulSoup parser.
    For allrecipes.com, force the print view by appending ?print= (or &print=).
    """
    if "allrecipes.com" in url and "print=" not in url:
        url += ("&" if "?" in url else "?") + "print="
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

# Only labels present in your HTML
_LABEL_MAP = {
    "prep time": "prep_time",
    "cook time": "cook_time",
    "additional time": "additional_time",
    "total time": "total_time",
    "servings": "yield",
}

def extract_basic_meta(soup: BeautifulSoup) -> dict:
    """
    Extract title and meta rows (prep/cook/additional/total/servings→yield).
    """
    out = {
        "title": None,
        "prep_time": None,
        "cook_time": None,
        "additional_time": None,
        "total_time": None,
        "yield": None,
    }

    h1 = soup.find("h1")
    if h1:
        out["title"] = h1.get_text(" ", strip=True) or None

    for row in soup.select(".mm-recipes-details__item"):
        lab_el = row.select_one(".mm-recipes-details__label")
        val_el = row.select_one(".mm-recipes-details__value")
        if not lab_el or not val_el:
            continue
        label = re.sub(r":\s*$", "", lab_el.get_text(" ", strip=True).lower())
        key = _LABEL_MAP.get(label)
        if not key:
            continue
        value = val_el.get_text(" ", strip=True)
        if value:
            out[key] = value

    return out

def extract_ingredients(soup: BeautifulSoup) -> list[dict]:
    """
    Extract ingredients as dicts: {qty, unit, name}.
    """
    results: list[dict] = []
    ul = soup.select_one("ul.mm-recipes-structured-ingredients__list")
    if not ul:
        return results

    for li in ul.select("li.mm-recipes-structured-ingredients__list-item"):
        q_el = li.select_one("span[data-ingredient-quantity='true']")
        u_el = li.select_one("span[data-ingredient-unit='true']")
        n_el = li.select_one("span[data-ingredient-name='true']")

        qty  = q_el.get_text(strip=True) if q_el else None
        unit = u_el.get_text(strip=True) if u_el else None
        name = n_el.get_text(" ", strip=True) if n_el else None

        if name:
            results.append({"qty": qty, "unit": unit, "name": name})

    return results

def main():
    if len(sys.argv) != 2:
        print("usage: python recipe_scraper.py <allrecipes_url>")
        sys.exit(1)

    soup = fetch_soup(sys.argv[1])
    meta = extract_basic_meta(soup)
    ings = extract_ingredients(soup)

    out = {
        "title": meta["title"],
        "prep_time": meta["prep_time"],
        "cook_time": meta["cook_time"],
        "additional_time": meta["additional_time"],
        "total_time": meta["total_time"],
        "yield": meta["yield"],
        "ingredients": ings,
    }

    # Write to file
    with open("recipe.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print("done")

if __name__ == "__main__":
    main()
