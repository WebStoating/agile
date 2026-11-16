"""Measure media with ffprobe."""
import json
from pathlib import Path
from typing import Dict

from pr_lib.proc import ToolError, run


def probe_duration(path: Path) -> float:
    cp = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
             timeout=60)
    if cp.returncode != 0:
        raise ToolError(f"ffprobe failed for {path}: {cp.stderr.strip()[:300]}")
    try:
        return float(json.loads(cp.stdout)["format"]["duration"])
    except (ValueError, KeyError, TypeError) as e:
        raise ToolError(f"ffprobe returned no duration for {path}") from e


def probe_streams(path: Path) -> Dict[str, int]:
    """Count the video and audio streams in a media file."""
    cp = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", str(path)],
             timeout=60)
    if cp.returncode != 0:
        raise ToolError(f"ffprobe failed for {path}: {cp.stderr.strip()[:300]}")
    try:
        streams = json.loads(cp.stdout).get("streams", [])
        kinds = [s["codec_type"] for s in streams]
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        raise ToolError(f"ffprobe returned unreadable streams for {path}") from e
    return {"video": kinds.count("video"), "audio": kinds.count("audio")}
