import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._path import PRESENT_ROOT, PRESENT_SCRIPTS

from pr_lib import deck as dk

CLI = PRESENT_SCRIPTS / "deck.py"
HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def make_deck(n=3, narration=None, **over):
    d = {"version": 1, "fps": 30, "width": 1920, "height": 1080, "pauseSeconds": 0.6,
         "voice": {"voice_id": "v1", "model_id": "m1"},
         "theme": {"primary": "#2563EB", "background": "#0B1220", "text": "#F8FAFC",
                   "font": "Inter", "logo": None},
         "slides": [{"type": "bullets", "title": f"S{i}", "bullets": ["a"],
                     "narration": narration or f"Narration {i}"} for i in range(n)]}
    d.update(over)
    return d


class DeckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.public = self.tmp / "public"

    def test_cache_key_stable_and_sensitive(self):
        k = dk.cache_key("v", "m", "hello")
        self.assertEqual(k, dk.cache_key("v", "m", "hello"))
        self.assertNotEqual(k, dk.cache_key("v2", "m", "hello"))
        self.assertNotEqual(k, dk.cache_key("v", "m2", "hello"))
        self.assertNotEqual(k, dk.cache_key("v", "m", "hellO"))
        text = "Café — 完了 ✅ “ok”"
        k2 = dk.cache_key("v", "m", text)
        self.assertRegex(k2, r"^[0-9a-f]{64}$")
        self.assertEqual(k2, dk.cache_key("v", "m", text))

    def test_prepare_reports_only_missing(self):
        deck = make_deck(3)
        key = dk.cache_key("v1", "m1", "Narration 1")
        (self.public / "audio").mkdir(parents=True)
        (self.public / "audio" / f"{key}.mp3").write_bytes(b"x")
        missing = dk.prepare(deck, self.public, self.tmp)
        self.assertEqual([m["index"] for m in missing], [0, 2])
        self.assertEqual(len(missing), 2)
        self.assertEqual(missing[0]["text"], "Narration 0")
        self.assertTrue(Path(missing[0]["path"]).is_absolute())
        self.assertTrue(all(s["audio"].startswith("audio/") for s in deck["slides"]))
        again = dk.prepare(deck, self.public, self.tmp)
        self.assertEqual([m["path"] for m in again], [m["path"] for m in missing])

    def test_prepare_creates_audio_folder(self):
        self.assertFalse(self.public.exists())
        dk.prepare(make_deck(1), self.public, self.tmp)
        self.assertTrue((self.public / "audio").is_dir())
        dk.prepare(make_deck(1), self.public, self.tmp)  # exists already: no error

    def test_prepare_removes_stale_part_files(self):
        audio = self.public / "audio"
        audio.mkdir(parents=True)
        (audio / "abc.mp3.part").write_bytes(b"half")
        (audio / "keep.mp3").write_bytes(b"x")
        dk.prepare(make_deck(1), self.public, self.tmp)
        self.assertFalse((audio / "abc.mp3.part").exists())
        self.assertTrue((audio / "keep.mp3").exists())

    def test_prepare_copies_logo(self):
        (self.tmp / "brand").mkdir()
        (self.tmp / "brand" / "logo.png").write_bytes(b"png")
        deck = make_deck(1)
        deck["theme"]["logo"] = "brand/logo.png"
        dk.prepare(deck, self.public, self.tmp)
        self.assertEqual((self.public / "logo.png").read_bytes(), b"png")
        self.assertEqual(deck["theme"]["logo"], "logo.png")

    def test_prepare_dedupes_identical_narration(self):
        deck = make_deck(3, narration="Same")
        missing = dk.prepare(deck, self.public, self.tmp)
        self.assertEqual([m["index"] for m in missing], [0])

    def test_cli_prepare_twice_with_logo_and_duplicates(self):
        (self.tmp / "brand").mkdir()
        (self.tmp / "brand" / "logo.png").write_bytes(b"png")
        deck = make_deck(2, narration="Same")
        deck["theme"]["logo"] = "brand/logo.png"
        f = self.tmp / "deck.json"
        f.write_text(json.dumps(deck), encoding="utf-8")
        cmd = [sys.executable, "-I", str(CLI), "prepare", "--deck", str(f),
               "--public-dir", str(self.public), "--root", str(self.tmp)]
        first = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        second = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))
        out = json.loads(second.stdout)
        self.assertEqual((len(out["missing"]), out["cached"]), (1, 0))
        self.assertEqual(json.loads(f.read_text(encoding="utf-8"))["theme"]["logo"], "logo.png")
        key = dk.cache_key("v1", "m1", "Same")
        (self.public / "audio").mkdir(parents=True, exist_ok=True)
        (self.public / "audio" / f"{key}.mp3").write_bytes(b"x")
        third = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(json.loads(third.stdout), {"missing": [], "cached": 1})

    def test_logo_errors(self):
        for logo in ("nope.png", "../x.png", str(self.tmp / "abs.png")):
            deck = make_deck(1)
            deck["theme"]["logo"] = logo
            with self.assertRaises(dk.DeckError, msg=logo):
                dk.prepare(deck, self.public, self.tmp)

    def test_finalize_missing_raises(self):
        deck = make_deck(2)
        dk.prepare(deck, self.public, self.tmp)
        with self.assertRaises(dk.DeckError) as cm:
            dk.finalize(deck, self.public, probe=lambda p: 1.0)
        self.assertIn("0", str(cm.exception))
        self.assertIn("1", str(cm.exception))

    def test_finalize_with_fake_probe(self):
        deck = make_deck(2)
        dk.prepare(deck, self.public, self.tmp)
        (self.public / "audio").mkdir(parents=True, exist_ok=True)
        for s in deck["slides"]:
            (self.public / s["audio"]).write_bytes(b"x")
        dk.finalize(deck, self.public, probe=lambda p: 1.23456)
        self.assertEqual(deck["slides"][0]["durationInSeconds"], 1.235)
        self.assertEqual(dk.total_frames(deck), 2 * math.ceil((1.235 + 0.6) * 30))

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
    def test_finalize_durations(self):
        deck = make_deck(2)
        dk.prepare(deck, self.public, self.tmp)
        (self.public / "audio").mkdir(parents=True, exist_ok=True)
        for s, secs in zip(deck["slides"], (1, 2)):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=d={secs}",
                            str(self.public / s["audio"])], check=True)
        dk.finalize(deck, self.public)
        d0, d1 = (s["durationInSeconds"] for s in deck["slides"])
        self.assertAlmostEqual(d0, 1.0, delta=0.1)
        self.assertAlmostEqual(d1, 2.0, delta=0.1)
        want = math.ceil(1.6 * 30) + math.ceil(2.6 * 30)
        self.assertLessEqual(abs(dk.total_frames(deck) - want), 3)

    def test_invalid_deck(self):
        cases = []
        d = make_deck(1); d["slides"][0]["type"] = "gallery"; cases.append(d)
        d = make_deck(1); d["slides"][0]["narration"] = "  "; cases.append(d)
        d = make_deck(1); del d["voice"]; cases.append(d)
        d = make_deck(1); d["voice"] = {"voice_id": "v"}; cases.append(d)
        d = make_deck(1); d["slides"] = []; cases.append(d)
        d = make_deck(1); del d["pauseSeconds"]; cases.append(d)
        d = make_deck(1); d["fps"] = 0; cases.append(d)
        for i, d in enumerate(cases):
            f = self.tmp / f"d{i}.json"
            f.write_text(json.dumps(d), encoding="utf-8")
            with self.assertRaises(dk.DeckError, msg=str(i)):
                dk.load_deck(f)

    def _assert_invalid(self, cases):
        for i, d in enumerate(cases):
            f = self.tmp / f"bad{i}.json"
            f.write_text(json.dumps(d), encoding="utf-8")
            with self.assertRaises(dk.DeckError, msg=str(i)):
                dk.load_deck(f)

    def test_invalid_numbers(self):
        cases = []
        for key in ("fps", "width", "height"):
            d = make_deck(1); d[key] = True; cases.append(d)
        d = make_deck(1); d["pauseSeconds"] = True; cases.append(d)
        for bad in ("NaN", "Infinity"):
            f = self.tmp / f"{bad}.json"
            f.write_text(json.dumps(make_deck(1)).replace('"pauseSeconds": 0.6',
                                                          f'"pauseSeconds": {bad}'), encoding="utf-8")
            with self.assertRaises(dk.DeckError, msg=bad):
                dk.load_deck(f)
        for bad in (True, -1, 0, "1", float("inf"), float("nan")):
            d = make_deck(1); d["slides"][0]["durationInSeconds"] = bad; cases.append(d)
        self._assert_invalid(cases)
        d = make_deck(1); d["slides"][0]["durationInSeconds"] = 2.5
        f = self.tmp / "ok.json"
        f.write_text(json.dumps(d), encoding="utf-8")
        dk.load_deck(f)

    def test_invalid_slide_fields(self):
        cases = []
        for t in ("title", "section", "bullets"):
            for bad in (None, "", "  ", 3):
                d = make_deck(1); d["slides"][0].update(type=t, title=bad, bullets=["a"]); cases.append(d)
        for bad in (None, [], ["a"] * 7, [1], ["ok", None], "a"):
            d = make_deck(1); d["slides"][0]["bullets"] = bad; cases.append(d)
        d = make_deck(1); del d["slides"][0]["bullets"]; cases.append(d)
        for bad in (None, 3):
            d = make_deck(1); d["slides"][0] = {"type": "quote", "quote": bad, "narration": "n"}; cases.append(d)
        d = make_deck(1); d["slides"][0] = {"type": "quote", "quote": "q", "title": 3, "narration": "n"}
        cases.append(d)
        d = make_deck(1); d["slides"][0].update(type="title", subtitle=5); cases.append(d)
        self._assert_invalid(cases)
        ok = make_deck(1)
        ok["slides"] = [{"type": "quote", "quote": "q", "narration": "n"},
                        {"type": "bullets", "title": "t", "bullets": ["a"] * 6, "narration": "n"},
                        {"type": "title", "title": "t", "subtitle": "s", "narration": "n"}]
        f = self.tmp / "ok.json"
        f.write_text(json.dumps(ok), encoding="utf-8")
        dk.load_deck(f)

    def test_invalid_theme(self):
        cases = []
        d = make_deck(1); del d["theme"]; cases.append(d)
        d = make_deck(1); d["theme"] = "dark"; cases.append(d)
        for key in ("primary", "background", "text", "font"):
            d = make_deck(1); del d["theme"][key]; cases.append(d)
            d = make_deck(1); d["theme"][key] = 1; cases.append(d)
        d = make_deck(1); d["theme"]["logo"] = 7; cases.append(d)
        self._assert_invalid(cases)

    def test_finalize_rejects_changed_narration(self):
        deck = make_deck(2)
        dk.prepare(deck, self.public, self.tmp)
        for s in deck["slides"]:
            (self.public / s["audio"]).write_bytes(b"x")
        deck["slides"][1]["narration"] = "Edited after prepare"
        with self.assertRaises(dk.DeckError) as cm:
            dk.finalize(deck, self.public, probe=lambda p: 1.0)
        self.assertIn("narration changed on slide 1; run prepare", str(cm.exception))
        deck = make_deck(1)
        deck["slides"][0]["audio"] = "audio/other.mp3"
        (self.public / "audio" / "other.mp3").write_bytes(b"x")
        with self.assertRaises(dk.DeckError):
            dk.finalize(deck, self.public, probe=lambda p: 1.0)

    def test_finalize_rejects_bad_probe(self):
        for bad in (0.0, -1.0, float("nan"), float("inf")):
            deck = make_deck(2)
            dk.prepare(deck, self.public, self.tmp)
            for s in deck["slides"]:
                (self.public / s["audio"]).write_bytes(b"x")
            values = iter((1.0, bad))
            with self.assertRaises(dk.DeckError, msg=str(bad)) as cm:
                dk.finalize(deck, self.public, probe=lambda p: next(values))
            self.assertIn("slide 1", str(cm.exception))

    def test_cli_non_ascii_console(self):
        f = self.tmp / "deck.json"
        f.write_text(json.dumps(make_deck(1, narration="Café — 完了 ✅"), ensure_ascii=False),
                     encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
        env["PYTHONUTF8"] = "0"
        cp = subprocess.run([sys.executable, "-I", str(CLI), "prepare", "--deck", str(f),
                             "--public-dir", str(self.public), "--root", str(self.tmp)],
                            capture_output=True, env=env)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertNotIn(b"UnicodeEncodeError", cp.stderr)
        out = json.loads(cp.stdout.decode("utf-8", "replace"))
        self.assertEqual(len(out["missing"]), 1)
        self.assertEqual(out["cached"], 0)

    def test_cli_error_exit(self):
        cp = subprocess.run([sys.executable, "-I", str(CLI), "finalize", "--deck",
                             str(self.tmp / "none.json"), "--public-dir", str(self.public)],
                            capture_output=True, text=True)
        self.assertEqual(cp.returncode, 1)
        self.assertIn("ERROR", cp.stderr)

    def test_example_deck_valid(self):
        deck = dk.load_deck(PRESENT_ROOT / "assets" / "deck.example.json")
        self.assertEqual([s["type"] for s in deck["slides"]], ["title", "section", "bullets", "quote"])


if __name__ == "__main__":
    unittest.main()
