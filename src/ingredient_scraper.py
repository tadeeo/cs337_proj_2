# ingredients.py
from bs4 import BeautifulSoup

def extract_ingredients(soup: BeautifulSoup) -> list[str]:
    """
    Extract ingredients as strings.
    Strategy:
      - Target: ul.mm-recipes-structured-ingredients__list > li.mm-recipes-structured-ingredients__list-item
      - For each li, read spans:
          data-ingredient-quantity="true"
          data-ingredient-unit="true"
          data-ingredient-name="true"
      - Join present parts with spaces.
      - Fallback: if the UL isn't found, collect all name spans as a last resort.

    Args:
      soup: BeautifulSoup parsed HTML.

    Returns:
      List of strings like: "1 cup vegetable oil", "2 tablespoons lime juice"
    """
    out: list[str] = []

    ul = soup.select_one("ul.mm-recipes-structured-ingredients__list")
    if ul:
        for li in ul.select("li.mm-recipes-structured-ingredients__list-item"):
            q = li.select_one("span[data-ingredient-quantity='true']")
            u = li.select_one("span[data-ingredient-unit='true']")
            n = li.select_one("span[data-ingredient-name='true']")

            parts = []
            if q and (qt := q.get_text(strip=True)):
                parts.append(qt)
            if u and (ut := u.get_text(strip=True)):
                parts.append(ut)
            if n and (nm := n.get_text(" ", strip=True)):
                parts.append(nm)

            line = " ".join(parts).strip()
            if line:
                out.append(line)

    # Minimal fallback: at least capture names if structure differs
    if not out:
        for name_span in soup.select("span[data-ingredient-name='true']"):
            nm = name_span.get_text(" ", strip=True)
            if nm:
                out.append(nm)

    return out
