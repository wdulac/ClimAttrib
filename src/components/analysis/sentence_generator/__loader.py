from functools import lru_cache
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


TEMPLATES_ROOT = Path(__file__).parent / "templates"

@lru_cache(maxsize=None)
def get_env(lang: str = "en") -> Environment:
    
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_ROOT / lang)),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,  # on rend du Markdown
    )
    return env


def register_filters(lang: str, **filters):

    env = get_env(lang)
    for name, fn in filters.items():
        env.filters[name] = fn


def render_template(name: str, variables: dict, lang: str = "en") -> str:

    env = get_env(lang)
    template = env.get_template(f"{name}.md")

    return template.render(**variables)