#!/usr/bin/env python3
"""Verify the rendered MP4 against the finalized deck.json.

Usage:
  python3 -I verify.py --video FILE --deck FILE

Prints `OK  <path>  <mm:ss>  <N> slides` and exits 0, or prints `PROBLEM <reason>` and exits 1.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pr_lib import deck as dk  # noqa: E402
from pr_lib import media  # noqa: E402
from pr_lib.console import safe_stdout  # noqa: E402
from pr_lib.proc import ToolError  # noqa: E402

TOLERANCE_SECONDS = 0.5


def check(video: Path, deck_path: Path) -> str:
    """Return the OK line, or raise ValueError with the problem."""
    try:
        deck = dk.load_deck(deck_path)
    except dk.DeckError as e:
        raise ValueError(f"deck unreadable: {e}") from e
    for i, s in enumerate(deck["slides"]):
        if not isinstance(s.get("durationInSeconds"), (int, float)):
            raise ValueError(f"deck not finalized: slide {i + 1} has no durationInSeconds")
    if not video.is_file():
        raise ValueError(f"video not found: {video}")
    try:
        streams = media.probe_streams(video)
        duration = media.probe_duration(video)
    except ToolError as e:
        raise ValueError(f"cannot probe video: {e}") from e
    if streams["video"] < 1:
        raise ValueError(f"no video stream in {video}")
    if streams["audio"] < 1:
        raise ValueError(f"no audio stream in {video}")
    expected = dk.total_frames(deck) / deck["fps"]
    if abs(duration - expected) > TOLERANCE_SECONDS:
        raise ValueError(f"duration {duration:.1f}s differs from expected {expected:.1f}s by more than "
                         f"{TOLERANCE_SECONDS}s")
    secs = int(round(duration))
    return f"OK  {video}  {secs // 60:02d}:{secs % 60:02d}  {len(deck['slides'])} slides"


def main(argv=None) -> int:
    safe_stdout()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--video", required=True)
    p.add_argument("--deck", required=True)
    args = p.parse_args(argv)
    try:
        print(check(Path(args.video), Path(args.deck)))
    except ValueError as e:
        print(f"PROBLEM {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
