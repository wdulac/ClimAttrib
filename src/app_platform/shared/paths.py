from pathlib import Path

def project_root(marker_files=(".git", "requirements.txt", "redis.conf", '.env')) -> Path:
    """
    Seeks any designated marker by crawling back up the folder tree.
    Returns project root directory.
    """

    p = Path(__file__).resolve()
    for parent in p.parents:
        if any((parent / m).exists() for m in marker_files):
            return parent
    # Fallback to 2nd order parent if all else fails
    return p.parents[-2]


ROOT = project_root()
SRC = ROOT / "src"
DATA = ROOT / "data"
COMPONENTS = SRC / "components"
ASSETS = SRC / "assets"
MARKDOWN_RESOURCES = COMPONENTS / "resources/md" # Holds text files used by components.resources sub-module