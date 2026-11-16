#!/usr/bin/env python3
"""Resolve presets, output paths and run folders for the present skill.

Usage:
  python3 -I settings.py resolve (--input FILE | --pasted) [--preset NAME] [--output FMT]
                                 [--cwd DIR] [--today YYYY-MM-DD]
  python3 -I settings.py save --root DIR --preset NAME --json-file FILE [--default]
"""
import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pr_lib import settings as st  # noqa: E402
from pr_lib.console import safe_stdout  # noqa: E402


def cmd_resolve(args) -> int:
    cwd = Path(args.cwd).resolve() if args.cwd else Path.cwd().resolve()
    today = date.fromisoformat(args.today) if args.today else date.today()
    input_path = Path(args.input).resolve() if args.input else None
    root = st.find_root(input_path.parent if input_path else cwd)
    if root is None:
        root = input_path.parent if input_path else cwd
    data = st.load(root)
    status, name = st.resolve_preset(data, args.preset)
    preset = data["presets"][name] if name else {}
    fmt = args.output or preset.get("output")
    out = st.resolve_output(fmt, input_path, cwd, name, today)
    settings_path = root / st.SETTINGS_NAME
    result = {
        "root": str(root),
        "settings_path": str(settings_path),
        "settings_exists": settings_path.is_file(),
        "status": status,
        "preset": name,
        "presets": sorted(data["presets"]),
        "context": preset.get("context"),
        "voice": preset.get("voice"),
        "theme": preset.get("theme"),
        "output_path": str(out),
        "output_exists": out.exists(),
        "output_parent_missing": not out.parent.exists(),
        "run_dir": str(st.run_dir(root, input_path, today)),
        "public_dir": str(root / ".present" / "public"),
        "remotion_dir": str(root / ".present" / "remotion"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_save(args) -> int:
    try:
        preset = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise st.SettingsError(f"cannot read {args.json_file}: {e}")
    if not isinstance(preset, dict):
        raise st.SettingsError("the preset JSON must be an object")
    print(st.save_preset(Path(args.root), args.preset, preset, args.default))
    return 0


def main(argv=None) -> int:
    safe_stdout()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve")
    g = r.add_mutually_exclusive_group(required=True)
    g.add_argument("--input")
    g.add_argument("--pasted", action="store_true")
    r.add_argument("--preset")
    r.add_argument("--output")
    r.add_argument("--cwd")
    r.add_argument("--today")
    r.set_defaults(func=cmd_resolve)
    s = sub.add_parser("save")
    s.add_argument("--root", required=True)
    s.add_argument("--preset", required=True)
    s.add_argument("--json-file", required=True)
    s.add_argument("--default", action="store_true")
    s.set_defaults(func=cmd_save)
    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except (st.SettingsError, ValueError, OSError) as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
