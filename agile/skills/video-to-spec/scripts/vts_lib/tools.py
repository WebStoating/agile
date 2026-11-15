"""Check that ffmpeg, ffprobe and the openai-whisper CLI are installed and usable."""
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Mapping, Optional, Tuple

from .proc import ToolError, run

MIN_FFMPEG = (5, 1)
MODEL_FILES = {"turbo": "large-v3-turbo.pt", "medium": "medium.pt"}
MODEL_SIZES = {"turbo": "~1.5 GB", "medium": "~1.4 GB"}
TOOLS = ("ffmpeg", "ffprobe", "whisper")

_VERSION_RE = re.compile(r"\b(?:ffmpeg|ffprobe) version n?(\d+)\.(\d+)")


def parse_ffmpeg_version(text: str) -> Optional[Tuple[int, int]]:
    m = _VERSION_RE.search(text)
    return (int(m.group(1)), int(m.group(2))) if m else None


def whisper_cache_dir(env: Mapping[str, str]) -> Path:
    base = env.get("XDG_CACHE_HOME")
    return (Path(base) if base else Path.home() / ".cache") / "whisper"


def install_hint(tool: str, platform: str) -> str:
    if tool == "whisper":
        cmd = ("brew install openai-whisper (https://formulae.brew.sh/formula/openai-whisper)"
               if platform == "darwin" else
               "pipx install openai-whisper (or: python3 -m pip install -U openai-whisper)")
        return f"install the openai-whisper CLI: {cmd}; the turbo model needs version 20240930 or newer"
    if platform == "darwin":
        cmd = "brew install ffmpeg"
    elif platform.startswith("win"):
        cmd = "winget install Gyan.FFmpeg"
    else:
        cmd = "sudo apt install ffmpeg (Debian/Ubuntu) or your distribution's ffmpeg package"
    return f"install ffmpeg {MIN_FFMPEG[0]}.{MIN_FFMPEG[1]} or newer (includes ffprobe): {cmd}"


def _check_ffmpeg_like(name: str, path: str, warnings: list) -> dict:
    info = {"found": True, "path": path, "version": None, "ok": False, "hint": None}
    try:
        out = run([path, "-version"], timeout=30)
    except ToolError as e:
        info["hint"] = f"{name} failed to run ({e}); " + install_hint(name, sys.platform)
        return info
    lines = (out.stdout or out.stderr).splitlines()
    first = lines[0] if lines else ""
    ver = parse_ffmpeg_version(first)
    if out.returncode != 0:
        info["hint"] = f"{name} -version exited {out.returncode}; " + install_hint(name, sys.platform)
    elif ver is None:
        info["ok"] = True
        warnings.append(f"{name}: could not read a version number ({first or 'no output'}); "
                        f"assuming a recent build (needs {MIN_FFMPEG[0]}.{MIN_FFMPEG[1]}+)")
    else:
        info["version"] = f"{ver[0]}.{ver[1]}"
        if ver >= MIN_FFMPEG:
            info["ok"] = True
        else:
            info["hint"] = f"{name} {info['version']} is too old; " + install_hint(name, sys.platform)
    return info


def _check_whisper(path: str) -> dict:
    info = {"found": True, "path": path, "version": None, "ok": False, "hint": None}
    try:
        out = run([path, "--help"], timeout=120)
    except ToolError as e:
        info["hint"] = f"whisper failed to run ({e}); " + install_hint("whisper", sys.platform)
        return info
    if out.returncode == 0:
        info["ok"] = True
    else:
        info["hint"] = f"whisper --help exited {out.returncode}; " + install_hint("whisper", sys.platform)
    return info


def check_all(env: Mapping[str, str] = os.environ) -> dict:
    warnings: list = []
    result_tools = {}
    for name in TOOLS:
        path = shutil.which(name, path=env.get("PATH"))
        if path is None:
            result_tools[name] = {"found": False, "path": None, "version": None, "ok": False,
                                  "hint": install_hint(name, sys.platform)}
        elif name == "whisper":
            result_tools[name] = _check_whisper(path)
        else:
            result_tools[name] = _check_ffmpeg_like(name, path, warnings)
    cache = whisper_cache_dir(env)
    models = {m: {"cached": (cache / f).is_file(), "path": str(cache / f)} for m, f in MODEL_FILES.items()}
    return {"ok": all(t["ok"] for t in result_tools.values()), "tools": result_tools,
            "models": models, "warnings": warnings}
