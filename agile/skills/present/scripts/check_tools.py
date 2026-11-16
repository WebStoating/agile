#!/usr/bin/env python3
"""Preflight for present: verify node, npx, ffmpeg, ffprobe, the ElevenLabs key and the Remotion license mode.

Usage: python3 -I check_tools.py [--root DIR] [--json]
Exit 0 when every tool is usable and the ElevenLabs key is available, 1 otherwise.
Key values are never printed.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path  # noqa: E402

from pr_lib.console import safe_stdout  # noqa: E402
from pr_lib.tools import check_all  # noqa: E402


def main(argv=None) -> int:
    safe_stdout()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", help="notes root whose .env may hold the keys")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    args = ap.parse_args(argv)
    res = check_all(os.environ, Path(args.root) if args.root else None)
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
    key = res["elevenlabs_key"]
    if key["present"]:
        print(f"OK       ELEVENLABS_API_KEY ({'environment' if key['source'] == 'env' else '.env'})")
    else:
        print("MISSING  ELEVENLABS_API_KEY - set it in your shell profile or run the ElevenLabs "
              "setup-api-key skill")
    if res["remotion_license"] == "key":
        print("LICENSE  Remotion: key from REMOTION_LICENSE_KEY")
    else:
        print("LICENSE  Remotion: free license (individuals and companies of up to 3 people)")
    for w in res["warnings"]:
        print(f"WARNING  {w}")
    print("All required tools are available." if res["ok"] else
          "Required tools or the ElevenLabs key are missing. Fix them, then run this check again.")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
