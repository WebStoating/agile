#!/usr/bin/env python3
"""Preflight for video-to-spec: verify ffmpeg, ffprobe and the openai-whisper CLI.

Usage: python3 -I check_tools.py [--json]
Exit 0 when every tool is usable, 1 otherwise (install hints are printed).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vts_lib.tools import MODEL_SIZES, check_all  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    args = ap.parse_args(argv)
    res = check_all()
    if args.json:
        print(json.dumps(res, indent=2))
        return 0 if res["ok"] else 1
    for name, t in res["tools"].items():
        if t["ok"]:
            print(" ".join(x for x in ("OK      ", name, t["version"], t["path"]) if x))
        elif not t["found"]:
            print(f"MISSING  {name} - {t['hint']}")
        else:
            print(f"PROBLEM  {name} {t['path']} - {t['hint']}")
    for w in res["warnings"]:
        print(f"WARNING  {w}")
    for model, m in res["models"].items():
        if m["cached"]:
            print(f"MODEL    {model}: downloaded")
        else:
            note = "only needed for non-English narration" if model == "medium" else "used for every transcription"
            print(f"MODEL    {model}: not downloaded yet - first use downloads {MODEL_SIZES[model]} ({note})")
    print("All required tools are available." if res["ok"] else
          "Required tools are missing or unusable. Install them, then run this check again.")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
