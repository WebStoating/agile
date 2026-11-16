import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._path import PRESENT_SCRIPTS
from tests.stubs import env_with_path, make_bin, version_stub

from pr_lib import tools

NODE = version_stub("v24.16.0")
NPX = version_stub("11.0.0")
FFMPEG = version_stub("ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers")
FFPROBE = version_stub("ffprobe version 9.0.2 Copyright (c) 2007-2026 the FFmpeg developers")
ALL = {"node": NODE, "npx": NPX, "ffmpeg": FFMPEG, "ffprobe": FFPROBE}
CLI = [sys.executable, "-I", str(PRESENT_SCRIPTS / "check_tools.py")]


class CheckToolsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def env(self, scripts=None, **extra):
        env = env_with_path(make_bin(self.tmp, scripts or ALL), **extra)
        for k in ("ELEVENLABS_API_KEY", "REMOTION_LICENSE_KEY"):
            env.pop(k, None)
        env.update(extra)
        return env

    def test_parse_node_version(self):
        self.assertEqual(tools.parse_node_version("v24.16.0"), (24, 16))
        self.assertIsNone(tools.parse_node_version("garbage"))

    def test_hints(self):
        self.assertIn("brew install node", tools.install_hint("node", "darwin"))
        self.assertIn("winget install OpenJS.NodeJS.LTS", tools.install_hint("npx", "win32"))
        self.assertIn("https://nodejs.org", tools.install_hint("node", "linux"))
        self.assertIn("brew install ffmpeg", tools.install_hint("ffmpeg", "darwin"))

    def test_all_present_key_in_env(self):
        res = tools.check_all(self.env(ELEVENLABS_API_KEY="sk-x"), None)
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["elevenlabs_key"], {"present": True, "source": "env"})
        self.assertEqual(res["remotion_license"], "free")

    def test_key_from_dotenv_and_license_key(self):
        root = self.tmp / "notes"
        root.mkdir()
        (root / ".env").write_text("ELEVENLABS_API_KEY=sk-secret-123\nREMOTION_LICENSE_KEY=rk-456\n")
        env = self.env()
        res = tools.check_all(env, root)
        self.assertEqual(res["elevenlabs_key"]["source"], ".env")
        self.assertEqual(res["remotion_license"], "key")
        self.assertTrue(res["ok"])
        for extra in ([], ["--json"]):
            cli = subprocess.run(CLI + ["--root", str(root)] + extra, env=env,
                                 capture_output=True, text=True)
            self.assertEqual(cli.returncode, 0, cli.stdout + cli.stderr)
            self.assertNotIn("sk-secret-123", cli.stdout + cli.stderr)
            self.assertNotIn("rk-456", cli.stdout + cli.stderr)

    def test_node_too_old(self):
        res = tools.check_all(self.env({**ALL, "node": version_stub("v16.20.0")},
                                       ELEVENLABS_API_KEY="k"), None)
        self.assertFalse(res["ok"])
        self.assertFalse(res["tools"]["node"]["ok"])
        self.assertIn("18", res["tools"]["node"]["hint"])

    def test_missing_key(self):
        cli = subprocess.run(CLI + ["--root", str(self.tmp)], env=self.env(),
                             capture_output=True, text=True)
        self.assertEqual(cli.returncode, 1)
        self.assertIn("MISSING  ELEVENLABS_API_KEY", cli.stdout)
        self.assertIn("LICENSE  Remotion: free license", cli.stdout)

    def test_missing_tool(self):
        res = tools.check_all(self.env({k: v for k, v in ALL.items() if k != "ffprobe"},
                                       ELEVENLABS_API_KEY="k"), None)
        self.assertFalse(res["ok"])
        self.assertFalse(res["tools"]["ffprobe"]["found"])


if __name__ == "__main__":
    unittest.main()
