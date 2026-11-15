"""ffprobe / ffmpeg wrappers."""
import json
from pathlib import Path

from .proc import ToolError, run, run_bytes
from .slides import THUMB_H, THUMB_W, parse_scene_times


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


def detect_scenes(video: Path, threshold: float) -> list:
    out = run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf", f"select='gt(scene,{threshold})',showinfo",
               "-fps_mode", "vfr", "-f", "null", "-"])
    if out.returncode != 0:
        raise ToolError(f"ffmpeg scene detection failed: {out.stderr.strip()[-500:]}")
    return parse_scene_times(out.stderr)


def grab_frame(video: Path, t: float, dest: Path, vf: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    out = run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
               "-vf", vf, "-q:v", "2", str(dest)], timeout=120)
    if out.returncode != 0 or not dest.is_file():
        raise ToolError(f"ffmpeg could not extract a frame at {t:.3f}s: {out.stderr.strip()[-500:]}")


def thumb(video: Path, t: float) -> bytes:
    out = run_bytes(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                     "-vf", f"scale={THUMB_W}:{THUMB_H},format=gray", "-f", "rawvideo", "-"], timeout=120)
    if out.returncode != 0 or len(out.stdout) < THUMB_W * THUMB_H:
        raise ToolError(f"ffmpeg could not read a thumbnail at {t:.3f}s")
    return out.stdout[:THUMB_W * THUMB_H]
