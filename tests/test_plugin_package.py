"""The plugin folder is what Claude Code and Codex copy into their cache; keep it clean and consistent."""
import json
import os
import unittest

from tests._path import PLUGIN_DIR, REPO_ROOT, SKILLS_DIR, skill_version

CLAUDE_MANIFEST = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
CODEX_MANIFEST = PLUGIN_DIR / "plugin.json"
DEV_MARKETPLACE = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
IGNORED = ("__pycache__", ".DS_Store")


class PluginPackageTests(unittest.TestCase):
    def test_manifests_agree_with_skills(self):
        claude = json.loads(CLAUDE_MANIFEST.read_text())
        codex = json.loads(CODEX_MANIFEST.read_text())
        self.assertEqual(claude, codex, "Claude Code and Codex manifests must be identical")
        self.assertEqual(claude["name"], "agile")
        self.assertEqual(claude["name"], PLUGIN_DIR.name)
        self.assertRegex(claude["version"], r"^\d+\.\d+\.\d+$")
        skills = [p for p in SKILLS_DIR.iterdir() if p.is_dir()]
        self.assertTrue(skills)
        for skill in skills:
            self.assertEqual(skill_version(skill), claude["version"], skill.name)

    def test_plugin_root_holds_only_shipped_files(self):
        top = sorted(p.name for p in PLUGIN_DIR.iterdir() if p.name not in IGNORED)
        self.assertEqual(top, [".claude-plugin", "plugin.json", "skills"])
        self.assertEqual(sorted(p.name for p in SKILLS_DIR.iterdir() if p.name not in IGNORED),
                         ["video-to-spec"])

    def test_no_symlink_escapes_plugin(self):
        real_root = os.path.realpath(PLUGIN_DIR)
        for dirpath, dirnames, filenames in os.walk(PLUGIN_DIR):
            for name in dirnames + filenames:
                p = os.path.join(dirpath, name)
                if os.path.islink(p):
                    target = os.path.realpath(p)
                    self.assertTrue(target == real_root or target.startswith(real_root + os.sep), p)

    def test_dev_marketplace_points_at_plugin(self):
        mp = json.loads(DEV_MARKETPLACE.read_text())
        (entry,) = mp["plugins"]
        self.assertEqual(entry["name"], "agile")
        self.assertEqual(entry["source"], {"source": "local", "path": "./agile"})

    def test_docs_ignored(self):
        lines = (REPO_ROOT / ".gitignore").read_text().splitlines()
        self.assertIn("docs/", lines)


if __name__ == "__main__":
    unittest.main()
