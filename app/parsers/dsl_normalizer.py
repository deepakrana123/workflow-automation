def normalize_multiline_dsl(raw_input: str) -> str:
    lines = [line.strip() for line in raw_input.splitlines() if line.strip()]
    normalized = []
    i = 0
    while i < len(lines):
        current = lines[i]
        # block header
        if current.endswith(":") and "->" not in current:
            if i + 1 >= len(lines):
                normalized.append(current)
                break

            next_line = lines[i + 1]

            merged = f"{current} {next_line}"

            normalized.append(merged)

            i += 2
            continue

        normalized.append(current)
        i += 1

    return "\n".join(normalized)
