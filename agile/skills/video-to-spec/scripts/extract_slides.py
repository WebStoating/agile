#!/usr/bin/env python3
"""Extract one complete frame per slide from a presentation video.

Usage:
  python3 -I extract_slides.py <video> --out <dir> [--mode auto|slides|interval] [--offset 0.4]
  python3 -I extract_slides.py <video> --out <dir> --retake N --at SECONDS
Writes <dir>/frames/slide_NN.jpg and <dir>/slides.json. Exit 0 ok, 1 failure.
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vts_lib.console import safe_stdout  # noqa: E402
from vts_lib import slides as S  # noqa: E402
from vts_lib.media import detect_scenes, grab_frame, probe, thumb  # noqa: E402
from vts_lib.proc import ToolError  # noqa: E402


def mmss(t: float) -> str:
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def print_table(index: dict) -> None:
    print(f"mode: {index['mode']}" + (f" (scene threshold {index['threshold']})" if index["threshold"] else ""))
    print("| file | time range | frame at |")
    print("|---|---|---|")
    for s in index["slides"]:
        print(f"| {s['file']} | {mmss(s['start'])}-{mmss(s['end'])} | {mmss(s['frame_time'])} |")


def extract(video: Path, out: Path, mode: str, offset: float) -> dict:
    info = probe(video)
    duration = info["duration"]
    if duration <= 0 or not info["width"]:
        raise ToolError(f"{video} has no readable video stream")
    vf = S.scale_filter(info["width"], info["height"])
    threshold, windows = None, None
    if mode in ("auto", "slides"):
        threshold, changes = S.choose_changes(duration, lambda t: detect_scenes(video, t))
        if threshold is not None:
            windows = S.slide_windows(changes, duration, offset)
        elif mode == "slides":
            if any(detect_scenes(video, t) for t in S.THRESHOLDS):
                raise ToolError("too many scene changes for a slide deck; rerun with --mode interval")
            windows = S.slide_windows([], duration, offset)
    if windows is None:
        mode = "interval"
        times = S.interval_times(duration)
        kept = [times[i] for i in S.dedupe([thumb(video, t) for t in times])]
        ends = kept[1:] + [duration]
        windows = [{"start": t, "end": round(e, 3), "frame_time": t} for t, e in zip(kept, ends)]
    else:
        mode = "slides"

    frames = out / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    for old in frames.glob("slide_*.jpg"):
        old.unlink()
    entries = []
    for i, w in enumerate(windows, 1):
        rel = f"frames/slide_{i:02d}.jpg"
        grab_frame(video, w["frame_time"], out / rel, vf)
        entries.append({"index": i, "file": rel, **w, "title": None})
    return {"video": str(video), "duration": duration, "width": info["width"], "height": info["height"],
            "mode": mode, "threshold": threshold, "offset": offset, "slides": entries}


def retake(video: Path, out: Path, n: int, at: float) -> dict:
    index = json.loads((out / "slides.json").read_text(encoding="utf-8"))
    if not 1 <= n <= len(index["slides"]):
        raise ToolError(f"there is no slide {n} (slides 1-{len(index['slides'])})")
    if not 0 <= at <= index["duration"]:
        raise ToolError(f"--at {at} is outside the video (0-{index['duration']:.1f}s)")
    slide = index["slides"][n - 1]
    grab_frame(video, at, out / slide["file"], S.scale_filter(index["width"], index["height"]))
    slide["frame_time"] = at
    return index


def main(argv=None) -> int:
    safe_stdout()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", choices=("auto", "slides", "interval"), default="auto")
    ap.add_argument("--offset", type=float, default=S.OFFSET)
    ap.add_argument("--retake", type=int, metavar="N")
    ap.add_argument("--at", type=float, metavar="SECONDS")
    a = ap.parse_args(argv)
    video, out = a.video.resolve(), a.out.resolve()
    if not video.is_file():
        print(f"error: video not found: {video}")
        return 1
    if (a.retake is None) != (a.at is None):
        print("error: --retake and --at must be used together")
        return 1
    try:
        if a.retake is not None:
            index = retake(video, out, a.retake, a.at)
        else:
            out.mkdir(parents=True, exist_ok=True)
            index = extract(video, out, a.mode, a.offset)
    except (ToolError, OSError, ValueError) as e:
        print(f"error: {e}")
        return 1
    (out / "slides.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print_table(index)
    print(f"index: {out / 'slides.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
