import requests
from bs4 import BeautifulSoup

def scrape_cooking_tools():
    """
    Scrape all utensil names and their full description from the Land O’Lakes equipment guide,
    and save as 'item : definition' pairs, one per line, in a plain text file.
    """
    url = "https://www.landolakes.com/kitchen-reference/equipment-guide/"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tools = []
    for section in soup.select("div.sectionRepeat"):
        h4 = section.find("h4")
        if not h4:
            continue
        name = h4.get_text(strip=True)

        desc = ""
        strong = section.find(lambda tag: tag.name == "strong" and "Description" in tag.get_text())
        if strong:
            collected = []
            for sibling in strong.parent.find_next_siblings():
                if sibling.name == "ul":
                    for li in sibling.find_all("li"):
                        collected.append(li.get_text(" ", strip=True))
                elif sibling.name in ["strong", "h4"]:
                    break
            desc = " ".join(collected)
        # One-line, clean whitespace, skip empty
        if name and desc:
            desc = " ".join(desc.split())
            tools.append(f"{name} : {desc}")

    with open("cooking_tools_withdesc.txt", "w", encoding="utf-8") as f:
        for line in tools:
            f.write(line + "\n")

    print(f"✅ Wrote {len(tools)} tools with descriptions to cooking_tools_withdesc.txt")

if __name__ == "__main__":
    scrape_cooking_tools()
