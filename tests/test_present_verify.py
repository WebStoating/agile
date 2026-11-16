import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._path import PRESENT_SCRIPTS

CLI = PRESENT_SCRIPTS / "verify.py"
HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def make_deck(duration=2.6, **slide_over):
    slide = {"type": "bullets", "title": "S", "bullets": ["a"], "narration": "n",
             "durationInSeconds": duration}
    slide.update(slide_over)
    return {"version": 1, "fps": 30, "width": 1920, "height": 1080, "pauseSeconds": 0.6,
            "voice": {"voice_id": "v1", "model_id": "m1"},
            "theme": {"primary": "#2563EB", "background": "#0B1220", "text": "#F8FAFC",
                      "font": "Inter", "logo": None},
            "slides": [slide]}


def make_mp4(path: Path, seconds=3.2, audio=True):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc=d={seconds}:s=160x90:r=30"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=d={seconds}", "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", str(seconds), str(path)]
    subprocess.run(cmd, check=True)


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def run_cli(self, video, deck):
        dp = self.tmp / "deck.json"
        if isinstance(deck, dict):
            dp.write_text(json.dumps(deck), encoding="utf-8")
        else:
            dp.write_text(deck, encoding="utf-8")
        return subprocess.run([sys.executable, "-I", str(CLI), "--video", str(video), "--deck", str(dp)],
                              capture_output=True, text=True)

    def test_ok(self):
        v = self.tmp / "o.mp4"
        make_mp4(v)
        r = self.run_cli(v, make_deck())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith("OK  "), r.stdout)
        self.assertIn("00:03", r.stdout)
        self.assertIn("1 slides", r.stdout)

    def test_no_audio(self):
        v = self.tmp / "o.mp4"
        make_mp4(v, audio=False)
        r = self.run_cli(v, make_deck())
        self.assertEqual(r.returncode, 1)
        self.assertIn("PROBLEM", r.stdout)
        self.assertIn("audio", r.stdout)

    def test_duration_mismatch(self):
        v = self.tmp / "o.mp4"
        make_mp4(v)
        r = self.run_cli(v, make_deck(duration=5.4))
        self.assertEqual(r.returncode, 1)
        self.assertIn("PROBLEM", r.stdout)

    def test_missing_file(self):
        r = self.run_cli(self.tmp / "nope.mp4", make_deck())
        self.assertEqual(r.returncode, 1)
        self.assertIn("PROBLEM", r.stdout)

    def test_deck_not_finalized(self):
        v = self.tmp / "o.mp4"
        make_mp4(v)
        deck = make_deck()
        del deck["slides"][0]["durationInSeconds"]
        r = self.run_cli(v, deck)
        self.assertEqual(r.returncode, 1)
        self.assertIn("PROBLEM deck not finalized", r.stdout)

    def test_invalid_deck(self):
        v = self.tmp / "o.mp4"
        make_mp4(v)
        r = self.run_cli(v, "not json")
        self.assertEqual(r.returncode, 1)
        self.assertIn("PROBLEM", r.stdout)
