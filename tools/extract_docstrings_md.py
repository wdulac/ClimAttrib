"""
Documentation generator: combines docs/architecture.md with module-level docstrings
extracted from src/ into a single Markdown file.

Usage (from the project root):
  python tools/extract_docstrings_md.py > docs/full_docs.md
"""
import ast
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
ARCH_DOC = ROOT_DIR / "docs" / "architecture.md"
ENV_DOC = ROOT_DIR / "docs" / "env_configuration.md"

# Modules are emitted in this order; files not listed here are appended alphabetically.
ORDERED_MODULES = [
    "app.py",
    "app_platform/__init__.py",
    "app_platform/compute/celery.py",
    "app_platform/compute/redis.py",
    "app_platform/shared/config.py",
    "app_platform/shared/paths.py",
    "app_platform/shared/tokens.py",
    "app_platform/shared/urls.py",
    "app_platform/web/__init__.py",
    "app_platform/web/redirects.py",
    "app_platform/web/api/__init__.py",
    "app_platform/web/api/register.py",
    "app_platform/web/api/geojson_tiles.py",
    "app_platform/web/api/download_csv.py",
    "app_platform/web/admin/__init__.py",
    "app_platform/web/admin/register.py",
    "app_platform/web/admin/__signature.py",
    "app_platform/web/admin/clear_cache.py",
    "app_platform/web/admin/restart.py",
    "app_platform/web/admin/stan_compile.py",
    "pages/home.py",
    "pages/analysis.py",
    "components/__init__.py",
    "components/home/__init__.py",
    "components/home/input_settings_top_bar.py",
    "components/home/location_selector.py",
    "components/analysis/__init__.py",
    "components/analysis/carousel.py",
    "components/analysis/__plotly_plots.py",
    "components/analysis/event_description/__init__.py",
    "components/analysis/event_description/analysis_description_component.py",
    "components/analysis/event_description/__event_key_figures.py",
    "components/analysis/event_description/__reverse_geocode.py",
    "components/analysis/event_description/__temperature_plot.py",
    "components/analysis/sentence_generator/__init__.py",
    "components/analysis/sentence_generator/builder.py",
    "components/analysis/sentence_generator/__data_models.py",
    "components/analysis/sentence_generator/__metrics.py",
    "components/analysis/sentence_generator/__loader.py",
    "components/analysis/sentence_generator/__phrases.py",
    "components/analysis/sentence_generator/__text_with_tooltip.py",
    "components/layout/__init__.py",
    "components/layout/disclaimer.py",
    "components/layout/header.py",
    "components/layout/footer.py",
    "components/resources/text_resources.py",
    "science/__init__.py",
    "science/attribution/__init__.py",
    "science/attribution/event_attribution.py",
    "science/attribution/__settings.py",
    "science/attribution/__data_loading.py",
    "science/attribution/__calendar_utils.py",
    "science/visualisation/__init__.py",
    "science/visualisation/attribution_plots.py",
    "science/visualisation/climatology_plots.py",
    "science/visualisation/__customdata.py",
    "science/visualisation/__plotly.py",
    "formatting/__init__.py",
    "formatting/metrics.py",
    "formatting/units.py",
    "formatting/__numbers.py",
    "formatting/__settings.py",
]


def extract_docstring(py_path: Path) -> str | None:
    try:
        text = py_path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except Exception:
        return None
    return ast.get_docstring(tree)


def format_module(rel_path: str, doc: str) -> str:

    # Exclude __init__.py from module name when docstring comes from a top-level dir
    if rel_path.split('/')[-1] == "__init__.py":
        rel_path = '/'.join(rel_path.split('/')[:-1]) + "/"

    return f"# Module `src/{rel_path}`\n\n{doc.strip()}\n"


def main():
    parts = []

    # --- Level 1: architecture document ---
    if ARCH_DOC.exists():
        parts.append(ARCH_DOC.read_text(encoding="utf-8").strip())

    # --- Level 1b: environment configuration ---
    if ENV_DOC.exists():
        parts.append(ENV_DOC.read_text(encoding="utf-8").strip())

    # --- Level 2: module docstrings in declared order ---
    seen = set()
    for rel in ORDERED_MODULES:
        p = SRC_DIR / rel
        if not p.exists():
            continue
        doc = extract_docstring(p)
        if doc:
            parts.append(format_module(rel, doc))
        seen.add(p.resolve())

    # --- Remaining files not in ORDERED_MODULES, alphabetically ---
    for dirpath, _, filenames in os.walk(SRC_DIR):
        for fn in sorted(filenames):
            if not fn.endswith(".py"):
                continue
            p = Path(dirpath) / fn
            if p.resolve() in seen:
                continue
            doc = extract_docstring(p)
            if doc:
                rel = str(p.relative_to(SRC_DIR))
                parts.append(format_module(rel, doc))

    print("\n\n---\n\n".join(parts))


if __name__ == "__main__":
    main()