"""Audio extraction and whisper transcription helpers."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

STATUS_FILE = "transcribe.status.json"


def audio_cmd(video: Path, wav: Path) -> List[str]:
    return ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(wav)]


def whisper_cmd(wav: Path, out_dir: Path, model: str, translate: bool) -> List[str]:
    cmd = ["whisper", str(wav), "--model", model, "--output_format", "json", "--output_dir", str(out_dir)]
    return cmd + ["--task", "translate"] if translate else cmd


def fingerprint(video: Path) -> dict:
    st = video.stat()
    return {"size": st.st_size, "mtime": int(st.st_mtime)}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_status(out: Path, **fields) -> None:
    p = out / STATUS_FILE
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    data.update(fields)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
