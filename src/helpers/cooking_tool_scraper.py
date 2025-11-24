import requests
from bs4 import BeautifulSoup

def scrape_cooking_tools():
    """Scrape all utensil names from the Land O’Lakes equipment guide."""
    url = "https://www.landolakes.com/kitchen-reference/equipment-guide/"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tools = []
    for section in soup.select("div.sectionRepeat"):
        h4 = section.find("h4")
        if h4:
            name = h4.get_text(strip=True)
            if name and name not in tools:
                tools.append(name)

    # Write to a plain text file, one per line
    with open("cooking_tools.txt", "w", encoding="utf-8") as f:
        for tool in tools:
            f.write(tool + "\n")

    print(f"✅ Wrote {len(tools)} cooking tools to cooking_tools.txt")

# Optional: call automatically if you want to generate file on run
if __name__ == "__main__":
    scrape_cooking_tools()
