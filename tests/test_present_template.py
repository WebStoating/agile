import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._path import PRESENT_ROOT, PRESENT_SCRIPTS

from pr_lib import deck as dk
from pr_lib import project as pj

TEMPLATE = PRESENT_ROOT / "assets" / "remotion-template"
CLI = PRESENT_SCRIPTS / "setup_project.py"


class TemplateTests(unittest.TestCase):
    def test_template_dir_location(self):
        self.assertEqual(pj.TEMPLATE_DIR.resolve(), TEMPLATE.resolve())
        meta = json.loads((TEMPLATE / "present-template.json").read_text(encoding="utf-8"))
        self.assertEqual(meta, {"templateVersion": "1"})

    def test_template_pins_exact_versions(self):
        pkg = json.loads((TEMPLATE / "package.json").read_text(encoding="utf-8"))
        deps = dict(pkg.get("dependencies", {}))
        deps.update(pkg.get("devDependencies", {}))
        self.assertTrue(deps)
        for name, ver in deps.items():
            self.assertRegex(ver, r"^\d+\.\d+\.\d+$", name)
        remotion = {n: v for n, v in deps.items() if n == "remotion" or n.startswith("@remotion/")}
        self.assertEqual(set(remotion), {"remotion", "@remotion/cli", "@remotion/google-fonts"})
        for name, ver in remotion.items():
            self.assertEqual(ver, "4.0.544", name)

    def test_template_types_match_contract(self):
        types = (TEMPLATE / "src" / "types.ts").read_text(encoding="utf-8")
        for key in ("pauseSeconds", "durationInSeconds", "audio", "narration", "primary",
                    "background", "text", "font", "logo"):
            self.assertIn(key, types)
        for t in dk.SLIDE_TYPES:
            self.assertIn(f'"{t}"', types)
        deck = dk.load_deck(TEMPLATE / "src" / "defaultDeck.json")
        for s in deck["slides"]:
            self.assertGreater(s["durationInSeconds"], 0)
            self.assertNotIn("audio", s)
        self.assertGreater(dk.total_frames(deck), 0)

    def test_timing_formula_shared(self):
        timing = (TEMPLATE / "src" / "timing.ts").read_text(encoding="utf-8")
        self.assertIn("Math.ceil(", timing)
        self.assertIn("pause", timing)
        self.assertIn("pr_lib/deck.py total_frames", timing)

    def test_no_node_modules_or_media_in_template(self):
        for dirpath, dirnames, filenames in os.walk(TEMPLATE):
            self.assertNotIn("node_modules", dirnames, dirpath)
            for name in filenames:
                self.assertFalse(name.lower().endswith((".mp3", ".mp4")), name)
                self.assertNotEqual(name, "package-lock.json")


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_ensure_project_create_update_current(self):
        rd = self.tmp / ".present" / "remotion"
        self.assertEqual(pj.ensure_project(rd), {"action": "created", "needs_install": True})
        self.assertTrue((rd / "package.json").is_file())
        self.assertTrue((rd / "src" / "Root.tsx").is_file())
        (rd / "node_modules" / "x").mkdir(parents=True)
        self.assertEqual(pj.ensure_project(rd), {"action": "current", "needs_install": False})
        (rd / "present-template.json").write_text('{"templateVersion": "0"}', encoding="utf-8")
        (rd / "stale.txt").write_text("old", encoding="utf-8")
        self.assertEqual(pj.ensure_project(rd), {"action": "updated", "needs_install": False})
        self.assertTrue((rd / "node_modules" / "x").is_dir())
        self.assertFalse((rd / "stale.txt").exists())
        meta = json.loads((rd / "present-template.json").read_text(encoding="utf-8"))
        self.assertEqual(meta, {"templateVersion": "1"})

    def test_update_with_changed_package_json_needs_install(self):
        rd = self.tmp / "remotion"
        pj.ensure_project(rd)
        (rd / "node_modules").mkdir()
        (rd / "package.json").write_text("{}", encoding="utf-8")
        (rd / "present-template.json").write_text('{"templateVersion": "0"}', encoding="utf-8")
        self.assertEqual(pj.ensure_project(rd), {"action": "updated", "needs_install": True})

    def test_add_gitignore(self):
        self.assertFalse(pj.add_gitignore(self.tmp))
        self.assertFalse((self.tmp / ".gitignore").exists())
        (self.tmp / ".git").mkdir()
        (self.tmp / ".gitignore").write_text("node_modules/", encoding="utf-8")
        self.assertTrue(pj.add_gitignore(self.tmp))
        self.assertFalse(pj.add_gitignore(self.tmp))
        lines = (self.tmp / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines.count(".present/"), 1)
        self.assertIn("node_modules/", lines)

    def test_cli_prints_json(self):
        (self.tmp / ".git").mkdir()
        r = subprocess.run([sys.executable, "-I", str(CLI), "--root", str(self.tmp), "--gitignore"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["action"], "created")
        self.assertTrue(out["needs_install"])
        self.assertTrue(out["gitignore_added"])
        self.assertEqual(Path(out["remotion_dir"]).resolve(),
                         (self.tmp / ".present" / "remotion").resolve())
        r = subprocess.run([sys.executable, "-I", str(CLI), "--root", str(self.tmp)],
                           capture_output=True, text=True)
        out = json.loads(r.stdout)
        self.assertEqual(out["action"], "current")
        self.assertFalse(out["gitignore_added"])


if __name__ == "__main__":
    unittest.main()
