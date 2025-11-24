def dedupe_items(input_path, output_path):
    seen = {}
    with open(input_path, 'r', encoding='utf-8') as infile:
        for line in infile:
            line = line.rstrip()
            if not line or ':' not in line:
                continue
            name, definition = line.split(':', 1)
            name = name.strip()
            definition = definition.strip()
            # Only keep the first encountered definition per unique item name
            if name and name not in seen:
                seen[name] = definition

    with open(output_path, 'w', encoding='utf-8') as outfile:
        for name, definition in seen.items():
            outfile.write(f"{name} : {definition}\n")

if __name__ == "__main__":
    dedupe_items("src/common_cooking_tools.txt", "common_cooking_tools.txt")
    print("✅ Finished writing common_cooking_tools.txt")
