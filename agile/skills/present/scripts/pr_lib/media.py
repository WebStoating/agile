"""Measure media with ffprobe."""
import json
from pathlib import Path

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
