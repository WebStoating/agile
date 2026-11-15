"""ffprobe / ffmpeg wrappers."""
import json
from pathlib import Path

from .proc import ToolError, run


def probe(video: Path) -> dict:
    out = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(video)],
              timeout=120)
    if out.returncode != 0:
        raise ToolError(f"ffprobe could not read {video}: {out.stderr.strip()[-500:]}")
    data = json.loads(out.stdout or "{}")
    streams = data.get("streams", [])
    vids = [s for s in streams if s.get("codec_type") == "video"]
    duration = float(data.get("format", {}).get("duration") or 0.0)
    return {
        "duration": duration,
        "width": int(vids[0].get("width", 0)) if vids else 0,
        "height": int(vids[0].get("height", 0)) if vids else 0,
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
    }
