import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._path import SCRIPTS
from tests.stubs import env_with_path, make_bin, version_stub

from vts_lib import tools

FFMPEG_OK = version_stub("ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers")
FFPROBE_OK = version_stub("ffprobe version 9.0.2 Copyright (c) 2007-2026 the FFmpeg developers")
WHISPER_OK = "print('usage: whisper [-h] [--model MODEL]')"


class VersionAndHintTests(unittest.TestCase):
    def test_parse_versions(self):
        self.assertEqual(tools.parse_ffmpeg_version("ffmpeg version 9.0.2 Copyright"), (9, 0))
        self.assertEqual(tools.parse_ffmpeg_version("ffmpeg version n6.1.1-3ubuntu5"), (6, 1))
        self.assertEqual(tools.parse_ffmpeg_version("ffprobe version 5.1 Copyright"), (5, 1))
        self.assertIsNone(tools.parse_ffmpeg_version("ffmpeg version N-112345-gabcdef"))

    def test_cache_dir(self):
        self.assertEqual(tools.whisper_cache_dir({"XDG_CACHE_HOME": "/x"}), Path("/x/whisper"))
        self.assertEqual(tools.whisper_cache_dir({}), Path.home() / ".cache" / "whisper")

    def test_hints(self):
        self.assertIn("brew install ffmpeg", tools.install_hint("ffmpeg", "darwin"))
        self.assertIn("apt install ffmpeg", tools.install_hint("ffmpeg", "linux"))
        self.assertIn("winget install Gyan.FFmpeg", tools.install_hint("ffmpeg", "win32"))
        for plat in ("darwin", "linux", "win32"):
            self.assertIn("pipx install openai-whisper", tools.install_hint("whisper", plat))


class CheckAllTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "cache" / "whisper").mkdir(parents=True)
        (self.tmp / "cache" / "whisper" / "large-v3-turbo.pt").write_bytes(b"x")

    def env(self, scripts):
        return env_with_path(make_bin(self.tmp, scripts), XDG_CACHE_HOME=str(self.tmp / "cache"))

    def test_all_present(self):
        res = tools.check_all(self.env({"ffmpeg": FFMPEG_OK, "ffprobe": FFPROBE_OK, "whisper": WHISPER_OK}))
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["tools"]["ffmpeg"]["version"], "9.0")
        self.assertTrue(res["models"]["turbo"]["cached"])
        self.assertFalse(res["models"]["medium"]["cached"])

    def test_missing_whisper(self):
        env = self.env({"ffmpeg": FFMPEG_OK, "ffprobe": FFPROBE_OK})
        res = tools.check_all(env)
        self.assertFalse(res["ok"])
        self.assertFalse(res["tools"]["whisper"]["found"])
        self.assertTrue(res["tools"]["whisper"]["hint"])
        cli = subprocess.run([sys.executable, "-I", str(SCRIPTS / "check_tools.py")],
                             env=env, capture_output=True, text=True)
        self.assertEqual(cli.returncode, 1)
        self.assertIn("pipx install openai-whisper", cli.stdout)

    def test_old_ffmpeg(self):
        res = tools.check_all(self.env({"ffmpeg": version_stub("ffmpeg version 4.4.2-0ubuntu0"),
                                        "ffprobe": FFPROBE_OK, "whisper": WHISPER_OK}))
        self.assertFalse(res["ok"])
        self.assertFalse(res["tools"]["ffmpeg"]["ok"])
        self.assertIn("5.1", res["tools"]["ffmpeg"]["hint"])

    def test_dev_build_warns(self):
        res = tools.check_all(self.env({"ffmpeg": version_stub("ffmpeg version N-112345-gabcdef Copyright"),
                                        "ffprobe": FFPROBE_OK, "whisper": WHISPER_OK}))
        self.assertTrue(res["tools"]["ffmpeg"]["ok"])
        self.assertTrue(res["ok"])
        self.assertEqual(len(res["warnings"]), 1)

    def test_whisper_broken(self):
        res = tools.check_all(self.env({"ffmpeg": FFMPEG_OK, "ffprobe": FFPROBE_OK,
                                        "whisper": "sys.exit(1)"}))
        self.assertFalse(res["tools"]["whisper"]["ok"])
        self.assertFalse(res["ok"])

    def test_cli_ok_json(self):
        env = self.env({"ffmpeg": FFMPEG_OK, "ffprobe": FFPROBE_OK, "whisper": WHISPER_OK})
        cli = subprocess.run([sys.executable, "-I", str(SCRIPTS / "check_tools.py"), "--json"],
                             env=env, capture_output=True, text=True)
        self.assertEqual(cli.returncode, 0, cli.stdout + cli.stderr)
        self.assertIn('"ok": true', cli.stdout)


if __name__ == "__main__":
    unittest.main()
