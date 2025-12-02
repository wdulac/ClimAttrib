"""
Simple extractor: parcourt `src/` et génère un fichier Markdown listant
uniquement la docstring de niveau module (sans importer le code).
Usage (depuis la racine du repo):
  python tools/extract_docstrings_md.py > docs/auto_docs.md
"""
import ast
import os
from pathlib import Path

SRC_DIR = Path("src")

def process_file(py_path: Path):
    try:
        text = py_path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except Exception:
        # skip files we cannot read/parse
        return None

    mod_doc = ast.get_docstring(tree)
    if not mod_doc:
        return None

    rel_path = py_path.relative_to(SRC_DIR.parent)
    # return module header + its top-level docstring
    return f"# Module `{rel_path}`\n\n{mod_doc.strip()}\n"

def main():
    parts = []
    for dirpath, _, filenames in os.walk(SRC_DIR):
        for fn in sorted(filenames):
            if fn.endswith(".py"):
                p = Path(dirpath) / fn
                res = process_file(p)
                if res:
                    parts.append(res)
    print("\n\n---\n\n".join(parts))

if __name__ == "__main__":
    main()