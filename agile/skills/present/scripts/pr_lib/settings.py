"""Project settings (.present.json): presets, output paths and run folders."""
import json
import os
import re
import stat
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional, Tuple

SETTINGS_NAME = ".present.json"
PLACEHOLDERS = ("stem", "date", "preset")
DEFAULT_FORMAT = "{stem}.mp4"
PASTED_STEM = "PRESENTATION"


class SettingsError(Exception):
    pass


def find_root(start: Path) -> Optional[Path]:
    start = Path(start).resolve()
    for folder in (start, *start.parents):
        if (folder / SETTINGS_NAME).is_file():
            return folder
    return None


def load(root: Path) -> dict:
    path = Path(root) / SETTINGS_NAME
    if not path.is_file():
        return {"version": 1, "presets": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise SettingsError(f"cannot read {path}: {e}")
    if not isinstance(data, dict):
        raise SettingsError(f"{path} must contain a JSON object")
    presets = data.setdefault("presets", {})
    if not isinstance(presets, dict):
        raise SettingsError(f"{path}: 'presets' must be an object")
    if data.get("default_preset") is not None and not isinstance(data["default_preset"], str):
        raise SettingsError(f"{path}: 'default_preset' must be a string")
    for name, preset in presets.items():
        if not isinstance(preset, dict):
            raise SettingsError(f"{path}: preset {name!r} must be an object")
        if preset.get("output") is not None and not isinstance(preset["output"], str):
            raise SettingsError(f"{path}: preset {name!r}: 'output' must be a string")
    data.setdefault("version", 1)
    return data


def _file_mode(path: Path) -> int:
    try:
        return stat.S_IMODE(path.stat().st_mode)
    except OSError:
        umask = os.umask(0)
        os.umask(umask)
        return 0o666 & ~umask


def save_preset(root: Path, name: str, preset: dict, make_default: bool) -> Path:
    data = load(root)
    data["presets"][name] = preset
    if make_default:
        data["default_preset"] = name
    path = Path(root) / SETTINGS_NAME
    mode = _file_mode(path)
    fd, tmp = tempfile.mkstemp(prefix=".present-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        os.chmod(tmp, mode)  # mkstemp creates 0600; keep the mode a plain write would give
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


def resolve_preset(settings: dict, requested: Optional[str]) -> Tuple[str, Optional[str]]:
    presets = settings.get("presets") or {}
    if not presets:
        return "none", None
    if requested:
        return ("ok", requested) if requested in presets else ("unknown", None)
    default = settings.get("default_preset")
    if default in presets:
        return "ok", default
    if len(presets) == 1:
        return "ok", next(iter(presets))
    return "ambiguous", None


def resolve_output(fmt: Optional[str], input_path: Optional[Path], cwd: Path,
                   preset: Optional[str], today: date) -> Path:
    fmt = fmt or DEFAULT_FORMAT
    values = {
        "stem": Path(input_path).stem if input_path else PASTED_STEM,
        "date": today.isoformat(),
        "preset": preset or "default",
    }

    def sub(m):
        key = m.group(1)
        if key not in values:
            raise SettingsError(f"unknown placeholder {{{key}}} in output format {fmt!r} "
                                f"(use {', '.join('{' + p + '}' for p in PLACEHOLDERS)})")
        return values[key]

    text = re.sub(r"\{(\w*)\}", sub, fmt)
    path = Path(text).expanduser()
    if not path.is_absolute():
        base = Path(input_path).parent if input_path else Path(cwd)
        path = base / path
    return path


def run_dir(root: Path, input_path: Optional[Path], today: date) -> Path:
    runs = Path(root) / ".present" / "runs"
    if input_path is None:
        return runs / "_pasted" / today.isoformat()
    try:
        rel = Path(input_path).resolve().relative_to(Path(root).resolve())
    except ValueError:
        rel = Path(Path(input_path).name)
    return runs / rel.with_suffix("")
