import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._path import SCRIPTS

from vts_lib import slides
from vts_lib.media import probe

SHOWINFO = """[Parsed_showinfo_1 @ 0x1] n:   0 pts:  48048 pts_time:4.004   duration: 1001
[Parsed_showinfo_1 @ 0x1] n:   1 pts:  96096 pts_time:8.008   duration: 1001
"""


class PureTests(unittest.TestCase):
    def test_parse_scene_times(self):
        self.assertEqual(slides.parse_scene_times(SHOWINFO), [4.004, 8.008])

    def test_collapse(self):
        self.assertEqual(slides.collapse([1.0, 1.5, 4.0, 4.2, 9.0]), [1.0, 4.0, 9.0])

    def test_choose_changes(self):
        many = [i * 0.5 + 0.5 for i in range(50)]
        fake = {0.02: many, 0.05: [4.0, 8.0], 0.1: []}
        self.assertEqual(slides.choose_changes(12.0, lambda t: fake[t]), (0.05, [4.0, 8.0]))
        self.assertEqual(slides.choose_changes(30.0, lambda t: many), (None, []))

    def test_choose_changes_prefers_most_sensitive(self):
        """Text-only slide changes score ~0.05; the most sensitive plausible threshold must win."""
        fake = {0.02: [5.0, 10.0], 0.05: [5.0], 0.1: []}
        self.assertEqual(slides.choose_changes(15.0, lambda t: fake[t]), (0.02, [5.0, 10.0]))

    def test_slide_windows(self):
        w = slides.slide_windows([4.0, 8.0], 12.0)
        self.assertEqual([x["start"] for x in w], [0.0, 4.0, 8.0])
        self.assertEqual([x["end"] for x in w], [4.0, 8.0, 12.0])
        for got, want in zip([x["frame_time"] for x in w], [3.6, 7.6, 11.6]):
            self.assertAlmostEqual(got, want)

    def test_single_slide_short_video(self):
        (w,) = slides.slide_windows([], 0.3)
        self.assertEqual(w["start"], 0.0)
        self.assertEqual(w["frame_time"], 0.0)

    def test_scale_filter(self):
        self.assertEqual(slides.scale_filter(1920, 1080), "scale=1568:-2")
        self.assertEqual(slides.scale_filter(1080, 1920), "scale=-2:1568")
        self.assertEqual(slides.scale_filter(1280, 720), "scale=iw:ih")

    def test_interval_times(self):
        self.assertEqual(slides.interval_times(12.0), [0.0, 5.0, 10.0])

    def test_dedupe(self):
        n = slides.THUMB_W * slides.THUMB_H
        a, a2, b = bytes([100]) * n, bytes([102]) * n, bytes([200]) * n
        self.assertEqual(slides.changed_fraction(a, b), 1.0)
        self.assertEqual(slides.changed_fraction(a, a2), 0.0)
        self.assertEqual(slides.dedupe([a, a2, b, b, a]), [0, 2, 4])

    def test_dedupe_keeps_text_only_change(self):
        """Two slides on the same background that differ in one short line of text are different slides."""
        w, h = slides.THUMB_W, slides.THUMB_H
        page = bytearray([255]) * (w * h)
        other = bytearray(page)
        for y in range(h // 2, h // 2 + max(2, h // 30)):          # one text line, ~1/3 of the width
            for x in range(w // 3, 2 * w // 3, 2):                 # glyph-like: every other pixel dark
                other[y * w + x] = 0
        self.assertEqual(slides.dedupe([bytes(page), bytes(other)]), [0, 1])

    def test_table_is_ascii(self):
        import extract_slides
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            extract_slides.print_table({"mode": "slides", "threshold": 0.02, "slides": [
                {"file": "frames/slide_01.jpg", "start": 0.0, "end": 5.0, "frame_time": 4.6}]})
        buf.getvalue().encode("ascii")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg not installed")
class ExtractSlidesIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.video = cls.tmp / "my talk ü.mp4"
        inputs = []
        for c in ("white", "black", "gray"):  # distinct luma; red and green are both gray 76
            inputs += ["-f", "lavfi", "-i", f"color=c={c}:s=640x360:d=4:r=25"]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs,
                        "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono",
                        "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]",
                        "-map", "[v]", "-map", "3:a", "-t", "12", "-c:v", "mpeg4", "-pix_fmt", "yuv420p",
                        str(cls.video)], check=True)

    def run_cli(self, out, *extra):
        return subprocess.run([sys.executable, "-I", str(SCRIPTS / "extract_slides.py"), str(self.video),
                               "--out", str(out), *extra], capture_output=True, text=True)

    def new_out(self):
        return Path(tempfile.mkdtemp(dir=self.tmp)) / "my talk ü-spec"

    def index(self, out):
        return json.loads((out / "slides.json").read_text())

    def test_slides_mode_end_to_end(self):
        out = self.new_out()
        r = self.run_cli(out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        idx = self.index(out)
        self.assertEqual(idx["mode"], "slides")
        self.assertEqual(len(idx["slides"]), 3)
        self.assertEqual(idx["slides"][0]["file"], "frames/slide_01.jpg")
        for s in idx["slides"]:
            self.assertIsNone(s["title"])
            self.assertGreater((out / s["file"]).stat().st_size, 0)
        self.assertTrue(probe(self.video)["has_audio"])

    def test_stale_frames_removed(self):
        out = self.new_out()
        (out / "frames").mkdir(parents=True)
        (out / "frames" / "slide_07.jpg").write_bytes(b"old")
        self.assertEqual(self.run_cli(out).returncode, 0)
        self.assertFalse((out / "frames" / "slide_07.jpg").exists())

    def test_retake(self):
        out = self.new_out()
        self.assertEqual(self.run_cli(out).returncode, 0)
        r = self.run_cli(out, "--retake", "2", "--at", "5.0")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.index(out)["slides"][1]["frame_time"], 5.0)
        self.assertEqual(self.run_cli(out, "--retake", "9", "--at", "1").returncode, 1)
        self.assertEqual(self.run_cli(out, "--retake", "1", "--at", "99").returncode, 1)

    def make_raw_video(self, name, slides_px, seconds_each=5, extra_audio=0):
        """White 640x360 slides; each slide is a list of (x0, x1, y0, y1) dark text-like bars."""
        w, h, fps = 640, 360, 5
        frames = bytearray()
        for bars in slides_px:
            img = bytearray([255]) * (w * h)
            for x0, x1, y0, y1 in bars:
                for y in range(y0, y1):
                    for x in range(x0, x1, 3):
                        img[y * w + x] = 0
            frames += bytes(img) * (fps * seconds_each)
        dur = len(slides_px) * seconds_each
        path = self.tmp / name
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray",
                        "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
                        "-f", "lavfi", "-t", str(dur + extra_audio), "-i", "anullsrc=r=16000:cl=mono",
                        "-map", "0:v", "-map", "1:a", "-c:v", "mpeg4", "-q:v", "2", "-pix_fmt", "yuv420p",
                        str(path)], input=bytes(frames), check=True)
        return path

    def run_on(self, video, out, *extra):
        return subprocess.run([sys.executable, "-I", str(SCRIPTS / "extract_slides.py"), str(video),
                               "--out", str(out), *extra], capture_output=True, text=True)

    def test_interval_mode_keeps_text_only_slides(self):
        title = (200, 440, 60, 90)
        video = self.make_raw_video("text deck.mp4", [[title, (120, 360, 200, 215)],
                                                      [title, (120, 520, 200, 215)],
                                                      [title, (120, 300, 240, 255)]])
        out = self.new_out()
        r = self.run_on(video, out, "--mode", "interval")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.index(out)["slides"]), 3)

    def test_audio_longer_than_video(self):
        video = self.make_raw_video("long audio.mp4", [[(100, 500, 100, 140)], [(100, 500, 200, 240)]],
                                    extra_audio=4)
        for mode in ("auto", "slides", "interval"):
            out = self.new_out()
            r = self.run_on(video, out, "--mode", mode)
            self.assertEqual(r.returncode, 0, f"{mode}: {r.stdout}{r.stderr}")
            idx = self.index(out)
            self.assertLessEqual(idx["duration"], 10.5, mode)
            for s in idx["slides"]:
                self.assertGreater((out / s["file"]).stat().st_size, 0)

    def test_interval_mode(self):
        out = self.new_out()
        r = self.run_cli(out, "--mode", "interval")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        idx = self.index(out)
        self.assertEqual(idx["mode"], "interval")
        self.assertEqual(len(idx["slides"]), 3)


if __name__ == "__main__":
    unittest.main()
