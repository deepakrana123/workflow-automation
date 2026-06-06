from pathlib import Path

BASE_DIR = Path(__file__).parent


def load_prompt(filename: str) -> str:
    path = BASE_DIR / "prompts" / filename
    return path.read_text(encoding="utf-8")


def build_prompt(filename: str, values: dict):
    template = load_prompt(filename)
    for key, value in values.items():
        template = template.replace("{" + key + "}", str(value))
    return template
