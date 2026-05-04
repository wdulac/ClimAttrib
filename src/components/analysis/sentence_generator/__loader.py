"""
Jinja2 template loader for the sentence generator.

Initialises a Jinja2 ``Environment`` pointing at the ``templates/`` directory adjacent
to this file, with ``trim_blocks=True`` and ``lstrip_blocks=True`` for clean Markdown
output. The environment is cached by language with ``lru_cache``.

``render_template(name, variables, lang)`` loads ``templates/{lang}/{name}.tmpl`` and
renders it with the supplied context dict. Templates follow the Jinja2 syntax.
"""

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


def render_template(name: str, variables: dict, lang: str = "en") -> str:

    env = get_env(lang)
    template = env.get_template(f"{name}.tmpl")

    return template.render(**variables)