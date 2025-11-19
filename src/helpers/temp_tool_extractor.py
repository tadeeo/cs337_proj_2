import re

pattern = re.compile(r"^(.*?)(?=\s*[:])")

results = []

with open("common_cooking_tools.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        match = pattern.match(line)
        if match:
            left_side = match.group(1).strip()
            if left_side:
                results.append(left_side)

# Write results to tools.txt
with open("tools.txt", "w", encoding="utf-8") as out:
    for item in results:
        out.write(item + "\n")
