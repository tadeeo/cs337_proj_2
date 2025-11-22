import sys, re, json
import requests
from bs4 import BeautifulSoup

# Labels observed in the HTML
_LABEL_MAP = {
    "prep time": "prep_time",
    "cook time": "cook_time",
    "additional time": "additional_time",
    "total time": "total_time",
    "servings": "yield",
}

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

def fetch_soup(url: str) -> BeautifulSoup:
    """Return BeautifulSoup for the page; force Allrecipes print view."""
    if "allrecipes.com" in url and "print=" not in url:
        url += ("&" if "?" in url else "?") + "print="
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def extract_basic_meta(soup: BeautifulSoup) -> dict:
    """Extract title and times/yield from the details rows."""
    meta = {
        "title": None,
        "prep_time": None,
        "cook_time": None,
        "additional_time": None,
        "total_time": None,
        "yield": None,
    }

    title_el = soup.find("h1")
    if title_el:
        meta["title"] = title_el.get_text(" ", strip=True) or None

    for row in soup.select(".mm-recipes-details__item"):
        label_el = row.select_one(".mm-recipes-details__label")
        value_el = row.select_one(".mm-recipes-details__value")
        if not label_el or not value_el:
            continue
        label = re.sub(r":\s*$", "", label_el.get_text(" ", strip=True).lower())
        key = _LABEL_MAP.get(label)
        if not key:
            continue
        value = value_el.get_text(" ", strip=True)
        if value:
            meta[key] = value

    return meta

def extract_ingredients(soup: BeautifulSoup) -> list[dict]:
    """Extract ingredients as {qty, unit, name} from the structured list."""
    items: list[dict] = []
    ingredients_ul = soup.select_one("ul.mm-recipes-structured-ingredients__list")
    if not ingredients_ul:
        return items

    for item in ingredients_ul.select("li.mm-recipes-structured-ingredients__list-item"):
        qty_el  = item.select_one("span[data-ingredient-quantity='true']")
        unit_el = item.select_one("span[data-ingredient-unit='true']")
        name_el = item.select_one("span[data-ingredient-name='true']")

        qty  = qty_el.get_text(strip=True) if qty_el else None
        unit = unit_el.get_text(strip=True) if unit_el else None
        name = name_el.get_text(" ", strip=True) if name_el else None

        if name:
            items.append({"qty": qty, "unit": unit, "name": name})

    return items

def extract_steps(soup: BeautifulSoup) -> list[dict]:
    """Extract ordered steps, then split each into sentence-level substeps."""
    steps: list[dict] = []

    container = soup.select_one("div.mm-recipes-steps")
    if not container:
        return steps

    ol = container.select_one("ol.mntl-sc-block-group--OL") or \
        container.select_one("ol[class*='mntl-sc-block-group--OL']")
    if not ol:
        return steps

    # Direct LI children are the step items
    li_nodes = ol.find_all("li", recursive=False)

    for i, li in enumerate(li_nodes, start=1):
        p = li.find("p")
        full_text = (p.get_text(" ", strip=True) if p else li.get_text(" ", strip=True)).strip()
        if not full_text:
            continue

        sentences = [s.strip() for s in _SENTENCE_SPLIT.split(full_text) if s.strip()]
        substeps = [{"sub_number": f"{i}.{j}", "text": s} for j, s in enumerate(sentences, start=1)]

        
        steps.append({
            "step_number": i,
            "text": full_text,
            "substeps": substeps
        })

    return steps

# _SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# def extract_steps(soup: BeautifulSoup) -> list[dict]:
#     """Extract top-level steps and split each into sentence substeps."""
#     steps: list[dict] = []

#     step_nodes = soup.select("ol.mm-recipes-steps__list li.mm-recipes-steps__item")
#     if not step_nodes:
#         step_nodes = soup.select("[class*='mm-recipes-steps__item']")

#     for i, node in enumerate(step_nodes, start=1):
#         p = node.find("p")
#         full_text = (p.get_text(" ", strip=True) if p else node.get_text(" ", strip=True)).strip()
#         if not full_text:
#             continue
#         sentences = [s.strip() for s in _SENTENCE_SPLIT.split(full_text) if s.strip()]
#         substeps = [{"sub_number": f"{i}.{j}", "text": s} for j, s in enumerate(sentences, start=1)]
#         steps.append({"step_number": i, "text": full_text, "substeps": substeps})

#     return steps

def main(url=None):
    if url is None:
        if len(sys.argv) != 2:
            print("usage: python recipe_scraper.py <allrecipes_url>")
            sys.exit(1)
        url = sys.argv[1]

    soup = fetch_soup(url)
    meta = extract_basic_meta(soup)
    ingredients = extract_ingredients(soup)
    steps = extract_steps(soup)

    data = {
        "title": meta["title"],
        "prep_time": meta["prep_time"],
        "cook_time": meta["cook_time"],
        "additional_time": meta["additional_time"],
        "total_time": meta["total_time"],
        "yield": meta["yield"],
        "ingredients": ingredients,
        "steps": steps,
    }

    with open("src/recipe.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print("Consider the recipe scraped!")

if __name__ == "__main__":
    main()
