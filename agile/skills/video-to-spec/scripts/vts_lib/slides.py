"""Pure logic for finding slide changes and choosing frames (no subprocesses here)."""
import re
from typing import Callable, List, Optional, Tuple

THRESHOLDS = (0.02, 0.05, 0.1)  # most sensitive first; text-only slide changes score ~0.05
MIN_GAP = 1.0          # seconds; scene changes closer than this are one change
SECONDS_PER_SLIDE = 3  # plausibility: at most one change per 3 s of video on average
OFFSET = 0.4           # take the frame this long before the next slide change
LONG_EDGE = 1568       # largest long edge vision models read at full detail
INTERVAL = 5.0         # seconds between frames when the video is not a slide deck
THUMB_W, THUMB_H = 160, 90
PIXEL_LEVEL = 32         # a thumbnail pixel "changed" when its gray value moves by more than this
DEDUPE_THRESHOLD = 0.003  # frames are duplicates when under 0.3% of pixels changed (one short text line is ~0.5%)

_PTS_RE = re.compile(r"pts_time:([0-9.]+)")


def parse_scene_times(stderr: str) -> List[float]:
    return [float(m.group(1)) for m in _PTS_RE.finditer(stderr)]


def collapse(times: List[float], min_gap: float = MIN_GAP) -> List[float]:
    kept: List[float] = []
    prev = 0.0
    for t in sorted(times):
        if t - prev >= min_gap:
            kept.append(t)
            prev = t
    return kept


def plausible(n: int, duration: float) -> bool:
    return 1 <= n <= duration / SECONDS_PER_SLIDE


def choose_changes(duration: float, detect: Callable[[float], List[float]]) -> Tuple[Optional[float], List[float]]:
    for t in THRESHOLDS:
        changes = [c for c in collapse(detect(t)) if c < duration]
        if plausible(len(changes), duration):
            return t, changes
    return None, []


def slide_windows(changes: List[float], duration: float, offset: float = OFFSET) -> List[dict]:
    bounds = [0.0, *changes, duration]
    return [{"start": round(s, 3), "end": round(e, 3), "frame_time": round(max(s, e - offset, 0.0), 3)}
            for s, e in zip(bounds, bounds[1:])]


def scale_filter(width: int, height: int, long_edge: int = LONG_EDGE) -> str:
    if max(width, height) <= long_edge:
        return "scale=iw:ih"
    return f"scale={long_edge}:-2" if width >= height else f"scale=-2:{long_edge}"


def interval_times(duration: float, step: float = INTERVAL) -> List[float]:
    times, t = [], 0.0
    while t < duration:
        times.append(round(t, 3))
        t += step
    return times or [0.0]


def changed_fraction(a: bytes, b: bytes, level: int = PIXEL_LEVEL) -> float:
    n = min(len(a), len(b))
    return sum(1 for x, y in zip(a[:n], b[:n]) if abs(x - y) > level) / n if n else 1.0


def dedupe(thumbs: List[bytes], threshold: float = DEDUPE_THRESHOLD) -> List[int]:
    kept: List[int] = []
    for i, t in enumerate(thumbs):
        if not kept or changed_fraction(thumbs[kept[-1]], t) >= threshold:
            kept.append(i)
    return kept
