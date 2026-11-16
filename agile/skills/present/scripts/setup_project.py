#!/usr/bin/env python3
"""Create or refresh the Remotion project in <root>/.present/remotion.

Usage:
  python3 -I setup_project.py --root DIR [--gitignore]

Prints JSON: {"remotion_dir", "action", "needs_install", "gitignore_added"}.
When needs_install is true, run `npm install` in remotion_dir.
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pr_lib import project  # noqa: E402
from pr_lib.console import safe_stdout  # noqa: E402


def main(argv=None) -> int:
    safe_stdout()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True)
    p.add_argument("--gitignore", action="store_true", help="add .present/ to <root>/.gitignore in a git checkout")
    args = p.parse_args(argv)
    root = Path(args.root).resolve()
    remotion_dir = root / ".present" / "remotion"
    try:
        result = project.ensure_project(remotion_dir)
        added = project.add_gitignore(root) if args.gitignore else False
    except OSError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 1
    out = {"remotion_dir": str(remotion_dir), "action": result["action"],
           "needs_install": result["needs_install"], "gitignore_added": added}
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
