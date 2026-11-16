"""Deck data: validation, content-hash audio paths and measured durations."""
import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Callable, List

from pr_lib.media import probe_duration

SLIDE_TYPES = ("title", "section", "bullets", "quote")


class DeckError(Exception):
    """The deck is invalid or incomplete."""


THEME_KEYS = ("primary", "background", "text", "font")
MAX_BULLETS = 6


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _is_text(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _check_slide(i: int, s: dict) -> None:
    kind = s["type"]
    if kind in ("title", "section", "bullets") and not _is_text(s.get("title")):
        raise DeckError(f"slide {i}: {kind} slides need a non-empty string title")
    if kind == "quote" and not isinstance(s.get("title", ""), str):
        raise DeckError(f"slide {i}: title must be a string")
    if not isinstance(s.get("subtitle", ""), str):
        raise DeckError(f"slide {i}: subtitle must be a string")
    if kind == "bullets":
        bullets = s.get("bullets")
        if (not isinstance(bullets, list) or not 1 <= len(bullets) <= MAX_BULLETS
                or not all(isinstance(b, str) for b in bullets)):
            raise DeckError(f"slide {i}: bullets must be a list of 1-{MAX_BULLETS} strings")
    if kind == "quote" and not isinstance(s.get("quote"), str):
        raise DeckError(f"slide {i}: quote slides need a string quote")
    if "durationInSeconds" in s:
        d = s["durationInSeconds"]
        if not _is_number(d) or d <= 0:
            raise DeckError(f"slide {i}: durationInSeconds must be a finite number > 0")


def _check_theme(theme) -> None:
    if not isinstance(theme, dict):
        raise DeckError("theme is required")
    for key in THEME_KEYS:
        if not isinstance(theme.get(key), str):
            raise DeckError(f"theme.{key} must be a string")
    logo = theme.get("logo")
    if logo is not None and not isinstance(logo, str):
        raise DeckError("theme.logo must be a path string or null")


def load_deck(path) -> dict:
    try:
        deck = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise DeckError(f"cannot read deck {path}: {e}") from e
    if not isinstance(deck, dict):
        raise DeckError("deck must be a JSON object")
    for key in ("fps", "width", "height"):
        if not _is_int(deck.get(key)) or deck[key] <= 0:
            raise DeckError(f"{key} must be a positive integer")
    pause = deck.get("pauseSeconds")
    if not _is_number(pause) or pause < 0:
        raise DeckError("pauseSeconds must be a finite number >= 0")
    voice = deck.get("voice")
    if not isinstance(voice, dict):
        raise DeckError("voice is required")
    for key in ("voice_id", "model_id"):
        if not isinstance(voice.get(key), str) or not voice[key]:
            raise DeckError(f"voice.{key} is required")
    _check_theme(deck.get("theme"))
    slides = deck.get("slides")
    if not isinstance(slides, list) or not slides:
        raise DeckError("slides must be a non-empty list")
    for i, s in enumerate(slides):
        if not isinstance(s, dict):
            raise DeckError(f"slide {i} must be an object")
        if s.get("type") not in SLIDE_TYPES:
            raise DeckError(f"slide {i}: type must be one of {', '.join(SLIDE_TYPES)}")
        n = s.get("narration")
        if not isinstance(n, str) or not n.strip():
            raise DeckError(f"slide {i}: narration must be a non-empty string")
        _check_slide(i, s)
    return deck


def cache_key(voice_id: str, model_id: str, text: str) -> str:
    payload = json.dumps([voice_id, model_id, text], ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _copy_logo(deck: dict, public_dir: Path, root: Path) -> None:
    theme = deck.get("theme")
    logo = theme.get("logo") if isinstance(theme, dict) else None
    if not logo:
        return
    if not isinstance(logo, str):
        raise DeckError("theme.logo must be a path string or null")
    rel = Path(logo)
    if rel.is_absolute() or ".." in rel.parts:
        raise DeckError(f"theme.logo must be relative to the notes root: {logo}")
    src = Path(root) / rel
    if (not src.is_file() and rel.parent == Path(".") and rel.stem == "logo"
            and (public_dir / logo).is_file()):
        return  # already prepared: theme.logo names the copy in public/
    if not src.is_file():
        raise DeckError(f"theme.logo not found: {src}")
    dest_name = "logo" + src.suffix.lower()
    public_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, public_dir / dest_name)
    theme["logo"] = dest_name


def prepare(deck: dict, public_dir: Path, root: Path) -> List[dict]:
    public_dir = Path(public_dir)
    voice = deck["voice"]
    _copy_logo(deck, public_dir, Path(root))
    audio_dir = public_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)  # the ElevenLabs CLI writes here
    for part in audio_dir.glob("*.part"):  # left by an interrupted text-to-speech call
        part.unlink()
    missing = []
    seen = set()
    for i, s in enumerate(deck["slides"]):
        key = cache_key(voice["voice_id"], voice["model_id"], s["narration"])
        s["audio"] = f"audio/{key}.mp3"
        s.pop("durationInSeconds", None)
        mp3 = public_dir / "audio" / f"{key}.mp3"
        if not mp3.is_file() and key not in seen:
            seen.add(key)
            missing.append({"index": i, "path": str(mp3.resolve()), "text": s["narration"]})
    return missing


def finalize(deck: dict, public_dir: Path, probe: Callable[[Path], float] = probe_duration) -> dict:
    public_dir = Path(public_dir)
    voice = deck["voice"]
    for i, s in enumerate(deck["slides"]):
        key = cache_key(voice["voice_id"], voice["model_id"], s["narration"])
        if s.get("audio") != f"audio/{key}.mp3":
            raise DeckError(f"narration changed on slide {i}; run prepare")
    absent = [i for i, s in enumerate(deck["slides"])
              if not s.get("audio") or not (public_dir / s["audio"]).is_file()]
    if absent:
        raise DeckError("missing audio for slides: " + ", ".join(str(i) for i in absent))
    for i, s in enumerate(deck["slides"]):
        seconds = probe(public_dir / s["audio"])
        if not _is_number(seconds) or seconds <= 0:
            raise DeckError(f"slide {i}: audio {s['audio']} has no usable duration ({seconds})")
        s["durationInSeconds"] = round(seconds, 3)
    return deck


def total_frames(deck: dict) -> int:
    fps, pause = deck["fps"], deck["pauseSeconds"]
    return sum(math.ceil((s["durationInSeconds"] + pause) * fps) for s in deck["slides"])
