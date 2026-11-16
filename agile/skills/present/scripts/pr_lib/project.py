"""Copy the Remotion template into <root>/.present/remotion and keep it current."""
import json
import shutil
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "remotion-template"
VERSION_FILE = "present-template.json"
KEEP = "node_modules"
_IGNORE = shutil.ignore_patterns(KEEP, "__pycache__", ".DS_Store")


def _template_version(folder: Path):
    try:
        return json.loads((folder / VERSION_FILE).read_text(encoding="utf-8")).get("templateVersion")
    except (OSError, ValueError, AttributeError):
        return None


def _read(path: Path):
    try:
        return path.read_bytes()
    except OSError:
        return None


def ensure_project(remotion_dir: Path) -> dict:
    """Create or refresh the Remotion project; node_modules/ survives a refresh."""
    remotion_dir = Path(remotion_dir)
    if not remotion_dir.is_dir():
        remotion_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(TEMPLATE_DIR, remotion_dir, ignore=_IGNORE)
        return {"action": "created", "needs_install": True}
    has_modules = (remotion_dir / KEEP).is_dir()
    if _template_version(remotion_dir) == _template_version(TEMPLATE_DIR):
        return {"action": "current", "needs_install": not has_modules}
    old_package = _read(remotion_dir / "package.json")
    for child in remotion_dir.iterdir():
        if child.name == KEEP:
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    shutil.copytree(TEMPLATE_DIR, remotion_dir, ignore=_IGNORE, dirs_exist_ok=True)
    changed = old_package != _read(remotion_dir / "package.json")
    return {"action": "updated", "needs_install": not has_modules or changed}


def add_gitignore(root: Path) -> bool:
    """Append `.present/` to root/.gitignore when root is a git checkout; True if the file changed."""
    root = Path(root)
    if not (root / ".git").exists():
        return False
    path = root / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if any(line.strip() in (".present/", ".present", "/.present/", "/.present") for line in text.splitlines()):
        return False
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text + ".present/\n", encoding="utf-8")
    return True
