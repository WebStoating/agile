"""Fake ffmpeg / ffprobe / whisper executables for tests. Real whisper never runs in the suite."""
import os
import stat
import sys
from pathlib import Path


def make_bin(tmp: Path, scripts: dict) -> Path:
    """Write one executable Python stub per {name: source} into tmp/bin and return that directory."""
    bindir = Path(tmp) / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    for name, source in scripts.items():
        p = bindir / name
        p.write_text(f"#!{sys.executable}\nimport json, os, sys\n{source}\n", encoding="utf-8")
        p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return bindir


def version_stub(line: str) -> str:
    return f"print({line!r})"


def env_with_path(bindir: Path, **extra) -> dict:
    env = dict(os.environ)
    env["PATH"] = str(bindir)
    env.update(extra)
    return env
