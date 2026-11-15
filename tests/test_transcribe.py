import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._path import SCRIPTS
from tests.stubs import env_with_path, make_bin

from vts_lib import transcript

FFPROBE = r'''
streams = [{"codec_type": "video", "width": 640, "height": 360}]
if not os.environ.get("STUB_NO_AUDIO"):
    streams.append({"codec_type": "audio"})
print(json.dumps({"streams": streams, "format": {"duration": "12.0"}}))
'''
FFMPEG = r'''
open(sys.argv[-1], "wb").write(b"RIFF0000WAVE")
'''
WHISPER = r'''
with open(os.environ["STUB_LOG"], "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\n")
code = int(os.environ.get("STUB_WHISPER_EXIT", "0"))
if code:
    for i in range(30):
        print(f"err-{i:02d}", file=sys.stderr)
    sys.exit(code)
out_dir = sys.argv[sys.argv.index("--output_dir") + 1]
stem = os.path.splitext(os.path.basename(sys.argv[1]))[0]
segs = [{"id": 0, "start": 0.0, "end": 4.2, "text": " Hello team."},
        {"id": 1, "start": 4.2, "end": 9.8, "text": " The report runs nightly."}]
with open(os.path.join(out_dir, stem + ".json"), "w") as f:
    json.dump({"text": "".join(s["text"] for s in segs), "segments": segs,
               "language": os.environ.get("STUB_LANG", "en")}, f)
'''


class CommandTests(unittest.TestCase):
    def test_cmds(self):
        self.assertEqual(transcript.audio_cmd(Path("v.mp4"), Path("o/audio.wav")),
                         ["ffmpeg", "-y", "-loglevel", "error", "-i", "v.mp4", "-vn", "-ac", "1",
                          "-ar", "16000", "o/audio.wav"])
        base = ["whisper", "o/audio.wav", "--model", "turbo", "--output_format", "json", "--output_dir", "o"]
        self.assertEqual(transcript.whisper_cmd(Path("o/audio.wav"), Path("o"), "turbo", False), base)
        self.assertEqual(transcript.whisper_cmd(Path("o/audio.wav"), Path("o"), "medium", True),
                         ["whisper", "o/audio.wav", "--model", "medium", "--output_format", "json",
                          "--output_dir", "o", "--task", "translate"])


class TranscribeCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.video = self.tmp / "demo talk.mp4"
        self.video.write_bytes(b"not really a video")
        self.out = self.tmp / "demo talk-spec"
        self.log = self.tmp / "whisper.log"
        self.bindir = make_bin(self.tmp, {"ffprobe": FFPROBE, "ffmpeg": FFMPEG, "whisper": WHISPER})

    def run_cli(self, *extra, **env):
        return subprocess.run([sys.executable, "-I", str(SCRIPTS / "transcribe.py"), str(self.video),
                               "--out", str(self.out), *extra],
                              env=env_with_path(self.bindir, STUB_LOG=str(self.log), **env),
                              capture_output=True, text=True)

    def calls(self):
        return [json.loads(l) for l in self.log.read_text().splitlines()] if self.log.exists() else []

    def status(self):
        return json.loads((self.out / "transcribe.status.json").read_text())

    def test_english_single_pass(self):
        r = self.run_cli()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        (call,) = self.calls()
        self.assertEqual(call[call.index("--model") + 1], "turbo")
        data = json.loads((self.out / "transcript.json").read_text())
        self.assertEqual(data["language"], "en")
        self.assertFalse(data["translated"])
        self.assertEqual(data["model"], "turbo")
        self.assertEqual(len(data["segments"]), 2)
        self.assertEqual(data["segments"][1], {"start": 4.2, "end": 9.8, "text": "The report runs nightly."})
        txt = (self.out / "transcript.txt").read_text()
        self.assertIn("Hello team.", txt)
        self.assertIn("The report runs nightly.", txt)
        self.assertFalse((self.out / "audio.wav").exists())
        self.assertFalse((self.out / "audio.json").exists())
        self.assertEqual(self.status()["stage"], "done")

    def test_non_english_translates(self):
        r = self.run_cli(STUB_LANG="de")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        first, second = self.calls()
        self.assertIn("turbo", first)
        self.assertEqual(second[second.index("--model") + 1], "medium")
        self.assertEqual(second[-2:], ["--task", "translate"])
        data = json.loads((self.out / "transcript.json").read_text())
        self.assertTrue(data["translated"])
        self.assertEqual(data["model"], "medium")
        self.assertEqual(data["language"], "de")

    def test_reuse_existing(self):
        self.assertEqual(self.run_cli().returncode, 0)
        r = self.run_cli()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(len(self.calls()), 1)
        self.assertIn("reusing existing transcript", r.stdout)

    def test_keep_audio(self):
        self.assertEqual(self.run_cli("--keep-audio").returncode, 0)
        self.assertTrue((self.out / "audio.wav").exists())

    def test_no_audio_exits_2(self):
        r = self.run_cli(STUB_NO_AUDIO="1")
        self.assertEqual(r.returncode, 2)
        self.assertIn("no audio", r.stdout.lower())
        self.assertEqual(self.calls(), [])

    def test_whisper_failure_reports_error(self):
        r = self.run_cli(STUB_WHISPER_EXIT="1")
        self.assertEqual(r.returncode, 1)
        out = r.stdout + r.stderr
        self.assertIn("err-29", out)
        self.assertIn("err-10", out)
        self.assertNotIn("err-09", out)
        st = self.status()
        self.assertEqual(st["stage"], "error")
        self.assertTrue(st["error"])


if __name__ == "__main__":
    unittest.main()
