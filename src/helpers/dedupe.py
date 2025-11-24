# dedupe_tools.py

def dedupe_tools(infile="src/tools.txt", outfile="src/tools.txt"):
    seen = set()
    unique_lines = []

    with open(infile, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if not name:
                continue

            key = name.lower()  # dedupe ignoring case
            if key in seen:
                continue

            seen.add(key)
            unique_lines.append(name)

    with open(outfile, "w", encoding="utf-8") as f:
        for name in unique_lines:
            f.write(name + "\n")


if __name__ == "__main__":
    dedupe_tools()
