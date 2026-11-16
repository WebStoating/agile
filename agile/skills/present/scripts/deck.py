#!/usr/bin/env python3
"""Prepare deck.json audio paths and measure narration durations.

Usage:
  python3 -I deck.py prepare  --deck FILE --public-dir DIR --root DIR
  python3 -I deck.py finalize --deck FILE --public-dir DIR
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pr_lib import deck as dk  # noqa: E402
from pr_lib.console import safe_stdout  # noqa: E402
from pr_lib.proc import ToolError  # noqa: E402


def _write(path: Path, deck: dict) -> None:
    path.write_text(json.dumps(deck, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    safe_stdout()
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("prepare")
    a.add_argument("--deck", required=True)
    a.add_argument("--public-dir", required=True)
    a.add_argument("--root", required=True)
    b = sub.add_parser("finalize")
    b.add_argument("--deck", required=True)
    b.add_argument("--public-dir", required=True)
    args = p.parse_args(argv)
    try:
        path = Path(args.deck)
        deck = dk.load_deck(path)
        public = Path(args.public_dir)
        if args.cmd == "prepare":
            missing = dk.prepare(deck, public, Path(args.root))
            _write(path, deck)
            present = {s["audio"] for s in deck["slides"] if (public / s["audio"]).is_file()}
            out = {"missing": missing, "cached": len(present)}
        else:
            dk.finalize(deck, public)
            _write(path, deck)
            out = {"slides": len(deck["slides"]), "seconds": dk.total_frames(deck) / deck["fps"]}
    except (dk.DeckError, ToolError) as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 1
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
