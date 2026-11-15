#!/usr/bin/env python3
"""Transcribe a video's narration to English with the openai-whisper CLI.

Usage: python3 -I transcribe.py <video> --out <dir> [--model turbo] [--keep-audio]
Writes <dir>/transcript.txt, <dir>/transcript.json and <dir>/transcribe.status.json.
Exit 0 ok (or reused), 1 tool/whisper failure, 2 the video has no audio stream.
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vts_lib.console import safe_stdout  # noqa: E402
from vts_lib.media import probe  # noqa: E402
from vts_lib.proc import ToolError, run  # noqa: E402
from vts_lib.transcript import audio_cmd, fingerprint, now, whisper_cmd, write_status  # noqa: E402

TRANSLATE_MODEL = "medium"


class Failure(Exception):
    pass


def tail(text: str, n: int = 20) -> str:
    return "\n".join(text.strip().splitlines()[-n:])


def whisper(wav: Path, out: Path, model: str, translate: bool) -> dict:
    res = run(whisper_cmd(wav, out, model, translate))
    if res.returncode != 0:
        raise Failure(f"whisper ({model}) exited {res.returncode}. Last lines of its output:\n"
                      f"{tail(res.stderr or res.stdout)}")
    produced = out / (wav.stem + ".json")
    if not produced.is_file():
        raise Failure(f"whisper finished but wrote no {produced.name}")
    data = json.loads(produced.read_text(encoding="utf-8"))
    produced.unlink()
    return data


def main(argv=None) -> int:
    safe_stdout()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--model", default="turbo")
    ap.add_argument("--keep-audio", action="store_true")
    a = ap.parse_args(argv)
    video, out = a.video.resolve(), a.out.resolve()
    if not video.is_file():
        print(f"error: video not found: {video}")
        return 1
    out.mkdir(parents=True, exist_ok=True)
    fp = fingerprint(video)
    existing = out / "transcript.json"
    if existing.is_file():
        try:
            if json.loads(existing.read_text(encoding="utf-8")).get("fingerprint") == fp:
                print(f"reusing existing transcript: {out / 'transcript.txt'}")
                return 0
        except ValueError:
            pass

    write_status(out, stage="audio", model=a.model, started=now(), finished=None, error=None)
    wav = out / "audio.wav"
    try:
        if not probe(video)["has_audio"]:
            write_status(out, stage="error", finished=now(), error="no audio stream")
            print("The video has no audio stream, so there is no narration to transcribe.")
            return 2
        res = run(audio_cmd(video, wav))
        if res.returncode != 0:
            raise Failure(f"ffmpeg could not extract audio:\n{tail(res.stderr)}")
        write_status(out, stage="transcribe")
        data = whisper(wav, out, a.model, translate=False)
        language, model, translated = data.get("language") or "unknown", a.model, False
        if language != "en":
            print(f"Detected language '{language}'; translating to English with the {TRANSLATE_MODEL} model.")
            write_status(out, stage="translate", model=TRANSLATE_MODEL)
            data = whisper(wav, out, TRANSLATE_MODEL, translate=True)
            model, translated = TRANSLATE_MODEL, True
    except (Failure, ToolError) as e:
        write_status(out, stage="error", finished=now(), error=str(e))
        print(f"error: {e}")
        return 1
    finally:
        if wav.exists() and not a.keep_audio:
            wav.unlink()

    segments = [{"start": float(s["start"]), "end": float(s["end"]), "text": s["text"].strip()}
                for s in data.get("segments", [])]
    text = "\n".join(s["text"] for s in segments) or (data.get("text") or "").strip()
    (out / "transcript.txt").write_text(text + "\n", encoding="utf-8")
    existing.write_text(json.dumps({"video": str(video), "fingerprint": fp, "language": language,
                                    "model": model, "translated": translated, "text": text,
                                    "segments": segments}, indent=2, ensure_ascii=False), encoding="utf-8")
    write_status(out, stage="done", finished=now())
    print(f"Transcript ({language}{', translated to English' if translated else ''}, {len(segments)} segments): "
          f"{out / 'transcript.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
