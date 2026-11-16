"""Make the skill's scripts/ importable for tests (mirrors what the entry scripts do)."""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "agile"
SKILLS_DIR = PLUGIN_DIR / "skills"
# ROOT is the video-to-spec skill directory: SKILL.md, scripts/, references/, assets/.
ROOT = SKILLS_DIR / "video-to-spec"
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
# The present skill directory and its scripts/.
PRESENT_ROOT = SKILLS_DIR / "present"
PRESENT_SCRIPTS = PRESENT_ROOT / "scripts"
if str(PRESENT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PRESENT_SCRIPTS))


def skill_version(skill_dir: Path) -> str:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r'^metadata:\n(?:  .*\n)*?  version: "([^"]+)"', text, re.M)
    assert m, f"{skill_dir.name}/SKILL.md metadata.version missing"
    return m.group(1)
