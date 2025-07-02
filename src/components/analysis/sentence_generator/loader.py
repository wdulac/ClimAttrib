from pathlib import Path

def load_template(name: str, lang="en"):
    path = Path(__file__).parent / "templates" / lang / f"{name}.md"
    return path.read_text()

def fill_template(template: str, variables: dict) -> str:
    return template.format(**variables)