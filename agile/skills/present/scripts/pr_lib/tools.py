"""Check node, npx, ffmpeg, ffprobe, the ElevenLabs key and the Remotion license mode."""
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Mapping, Optional, Tuple

from .envfile import source
from .proc import ToolError, run

MIN_NODE = (18, 0)
TOOLS = ("node", "npx", "ffmpeg", "ffprobe")

_NODE_RE = re.compile(r"v?(\d+)\.(\d+)")


def parse_node_version(text: str) -> Optional[Tuple[int, int]]:
    m = _NODE_RE.search(text or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def install_hint(tool: str, platform: str) -> str:
    if tool in ("node", "npx"):
        if platform == "darwin":
            cmd = "brew install node"
        elif platform.startswith("win"):
            cmd = "winget install OpenJS.NodeJS.LTS"
        else:
            cmd = "your distribution's nodejs package or https://nodejs.org"
        return f"install Node.js {MIN_NODE[0]} or newer (includes npx): {cmd}"
    if platform == "darwin":
        cmd = "brew install ffmpeg"
    elif platform.startswith("win"):
        cmd = "winget install Gyan.FFmpeg"
    else:
        cmd = "sudo apt install ffmpeg (Debian/Ubuntu) or your distribution's ffmpeg package"
    return f"install ffmpeg 5.1 or newer (includes ffprobe): {cmd}"


def _check(name: str, path: str, warnings: list) -> dict:
    info = {"found": True, "path": path, "version": None, "ok": False, "hint": None}
    flag = "-version" if name in ("ffmpeg", "ffprobe") else "--version"
    try:
        out = run([path, flag], timeout=30)
    except ToolError as e:
        info["hint"] = f"{name} failed to run ({e}); " + install_hint(name, sys.platform)
        return info
    if out.returncode != 0:
        info["hint"] = f"{name} {flag} exited {out.returncode}; " + install_hint(name, sys.platform)
        return info
    first = ((out.stdout or out.stderr).splitlines() or [""])[0].strip()
    if name == "node":
        ver = parse_node_version(first)
        if ver is None:
            info["ok"] = True
            warnings.append(f"node: could not read a version number ({first or 'no output'}); "
                            f"assuming a recent build (needs {MIN_NODE[0]}+)")
        else:
            info["version"] = f"{ver[0]}.{ver[1]}"
            if ver >= MIN_NODE:
                info["ok"] = True
            else:
                info["hint"] = f"node {info['version']} is too old; " + install_hint(name, sys.platform)
    else:
        info["ok"] = True
        if name == "npx":
            info["version"] = first or None
    return info


def check_all(env: Mapping[str, str] = os.environ, root: Optional[Path] = None) -> dict:
    warnings: list = []
    result_tools = {}
    for name in TOOLS:
        path = shutil.which(name, path=env.get("PATH"))
        if path is None:
            result_tools[name] = {"found": False, "path": None, "version": None, "ok": False,
                                  "hint": install_hint(name, sys.platform)}
        else:
            result_tools[name] = _check(name, path, warnings)
    dotenv = Path(root) / ".env" if root is not None else None
    key_source = source("ELEVENLABS_API_KEY", env, dotenv)
    license_mode = "key" if source("REMOTION_LICENSE_KEY", env, dotenv) else "free"
    present = key_source is not None
    return {"ok": present and all(t["ok"] for t in result_tools.values()), "tools": result_tools,
            "elevenlabs_key": {"present": present, "source": key_source},
            "remotion_license": license_mode, "warnings": warnings}
