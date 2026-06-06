import re

STEP_HEADER_PATTERN = re.compile(
    r"(@\d+)(?:\s+@depends\((.*?)\))?\s*:",
    re.IGNORECASE,
)


def decompose_workflow(text: str):

    matches = list(STEP_HEADER_PATTERN.finditer(text))

    if not matches:
        return []

    steps = []

    for index, match in enumerate(matches):

        step_id = match.group(1)

        depends_raw = match.group(2)

        content_start = match.end()

        content_end = (
            matches[index + 1].start() if index + 1 < len(matches) else len(text)
        )

        raw_step_text = text[content_start:content_end].strip()

        depends_on = []

        if depends_raw:

            depends_on = [dep.strip() for dep in depends_raw.split(",") if dep.strip()]

        steps.append(
            {
                "id": step_id,
                "depends_on": depends_on,
                "text": raw_step_text,
            }
        )

    return steps


def validate_decomposition(steps):

    seen = set()

    for step in steps:

        step_id = step["id"]

        if step_id in seen:

            raise ValueError(f"Duplicate step id: {step_id}")

        seen.add(step_id)


def parse_workflow_structure(text: str):

    steps = decompose_workflow(text)

    validate_decomposition(steps)

    return steps
