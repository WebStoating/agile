import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tests._path import PRESENT_SCRIPTS
from pr_lib import settings
from pr_lib.settings import SettingsError

TODAY = date(2026, 11, 16)
CLI = PRESENT_SCRIPTS / "settings.py"


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name).resolve()

    def test_find_root_from_week_subfolder(self):
        week = self.root / "week-46"
        week.mkdir()
        (week / "2026-11-16.md").write_text("x", encoding="utf-8")
        self.assertIsNone(settings.find_root(week))
        (self.root / ".present.json").write_text("{}", encoding="utf-8")
        self.assertEqual(settings.find_root(week), self.root)

    def test_resolve_preset_order(self):
        self.assertEqual(settings.resolve_preset({"presets": {"a": {}}}, None), ("ok", "a"))
        two = {"presets": {"a": {}, "b": {}}}
        self.assertEqual(settings.resolve_preset(two, None), ("ambiguous", None))
        self.assertEqual(settings.resolve_preset({**two, "default_preset": "b"}, None), ("ok", "b"))
        self.assertEqual(settings.resolve_preset(two, "x"), ("unknown", None))
        self.assertEqual(settings.resolve_preset({"presets": {}}, None), ("none", None))

    def test_resolve_output(self):
        w = self.root / "w"
        f = w / "notes.md"
        self.assertEqual(settings.resolve_output(None, f, self.root, None, TODAY), w / "notes.mp4")
        self.assertEqual(settings.resolve_output(None, None, self.root, None, TODAY),
                         self.root / "PRESENTATION.mp4")
        self.assertEqual(settings.resolve_output("{preset}-{date}.mp4", f, self.root, "standup", TODAY),
                         w / "standup-2026-11-16.mp4")
        self.assertEqual(settings.resolve_output("{preset}.mp4", f, self.root, None, TODAY),
                         w / "default.mp4")
        with self.assertRaises(SettingsError) as cm:
            settings.resolve_output("{week}.mp4", f, self.root, None, TODAY)
        self.assertIn("week", str(cm.exception))

    def test_run_dir_no_collision(self):
        a = settings.run_dir(self.root, self.root / "week-45" / "monday.md", TODAY)
        b = settings.run_dir(self.root, self.root / "week-46" / "monday.md", TODAY)
        self.assertEqual(a, self.root / ".present" / "runs" / "week-45" / "monday")
        self.assertEqual(b, self.root / ".present" / "runs" / "week-46" / "monday")
        self.assertEqual(settings.run_dir(self.root, None, TODAY),
                         self.root / ".present" / "runs" / "_pasted" / "2026-11-16")

    def test_save_merges_and_is_atomic(self):
        settings.save_preset(self.root, "standup", {"voice": "v1"}, False)
        path = settings.save_preset(self.root, "weekly", {"voice": "v2"}, True)
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(set(data["presets"]), {"standup", "weekly"})
        self.assertEqual(data["default_preset"], "weekly")
        self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), [".present.json"])

    @unittest.skipIf(os.name == "nt", "POSIX file modes")
    def test_save_keeps_file_mode(self):
        old = os.umask(0o022)
        try:
            path = settings.save_preset(self.root, "a", {}, False)
        finally:
            os.umask(old)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o644)
        path.chmod(0o640)
        settings.save_preset(self.root, "b", {}, False)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_corrupt_file(self):
        p = self.root / ".present.json"
        p.write_text("{oops", encoding="utf-8")
        with self.assertRaises(SettingsError):
            settings.load(self.root)
        with self.assertRaises(SettingsError):
            settings.save_preset(self.root, "a", {}, False)
        self.assertEqual(p.read_text(encoding="utf-8"), "{oops")

    def test_non_object_presets(self):
        (self.root / ".present.json").write_text('{"presets": []}', encoding="utf-8")
        with self.assertRaises(SettingsError):
            settings.load(self.root)

    def _cli(self, *args):
        return subprocess.run([sys.executable, "-I", str(CLI), *args], capture_output=True,
                              text=True, encoding="utf-8")

    def test_cli_resolve(self):
        (self.root / "w").mkdir()
        notes = self.root / "w" / "notes.md"
        notes.write_text("x", encoding="utf-8")
        cfg = self.root / ".present.json"
        cfg.write_text(json.dumps({"version": 1, "presets": {"a": {"voice": "v", "theme": "t"}}}),
                       encoding="utf-8")
        r = self._cli("resolve", "--input", str(notes), "--today", "2026-11-16")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["preset"], "a")
        self.assertEqual(out["voice"], "v")
        self.assertEqual(out["presets"], ["a"])
        self.assertTrue(out["output_path"].endswith("notes.mp4"))
        self.assertFalse(out["output_exists"])
        self.assertFalse(out["output_parent_missing"])
        self.assertTrue(out["run_dir"].endswith("/.present/runs/w/notes"))
        self.assertTrue(out["settings_exists"])
        cfg.write_text("{oops", encoding="utf-8")
        r = self._cli("resolve", "--input", str(notes))
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stderr.startswith("ERROR"))

    def test_cli_resolve_no_settings_and_save(self):
        notes = self.root / "n.md"
        notes.write_text("x", encoding="utf-8")
        r = self._cli("resolve", "--input", str(notes), "--output", "out/{stem}.mp4")
        out = json.loads(r.stdout)
        self.assertEqual(out["status"], "none")
        self.assertIsNone(out["preset"])
        self.assertTrue(out["output_parent_missing"])
        self.assertEqual(out["root"], str(self.root))
        pj = self.root / "p.json"
        pj.write_text('{"voice": "x"}', encoding="utf-8")
        r = self._cli("save", "--root", str(self.root), "--preset", "s", "--json-file", str(pj), "--default")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.strip().endswith(".present.json"))
        r = self._cli("resolve", "--pasted", "--cwd", str(self.root))
        out = json.loads(r.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertTrue(out["output_path"].endswith("PRESENTATION.mp4"))


if __name__ == "__main__":
    unittest.main()
