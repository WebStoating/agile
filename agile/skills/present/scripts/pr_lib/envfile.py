"""Read values from the environment and a project `.env` file. Never prints values."""
from pathlib import Path
from typing import Dict, Mapping, Optional


def parse_dotenv(text: str) -> Dict[str, str]:
    out = {}  # type: Dict[str, str]
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        close = value.find(value[0], 1) if value[:1] in ("\"", "'") else -1
        rest = value[close + 1:].lstrip() if close != -1 else ""
        if close != -1 and (not rest or rest.startswith("#")):
            value = value[1:close]
        elif len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]
        else:
            cut = value.find(" #")
            if cut != -1:
                value = value[:cut]
            value = value.strip()
        out[key] = value
    return out


def lookup(name: str, env: Mapping[str, str], dotenv: Optional[Path]) -> Optional[str]:
    value = env.get(name)
    if value:
        return value
    if dotenv is None:
        return None
    try:
        text = dotenv.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return parse_dotenv(text).get(name) or None


def source(name: str, env: Mapping[str, str], dotenv: Optional[Path]) -> Optional[str]:
    """Where `lookup` would find a non-empty value: "env", ".env" or None."""
    if env.get(name):
        return "env"
    return ".env" if lookup(name, {}, dotenv) else None
