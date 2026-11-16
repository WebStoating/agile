import re
import unittest

from tests._path import PRESENT_ROOT
from tests.test_skill_md import AGENT_SPECIFIC, frontmatter

SKILL = PRESENT_ROOT / "SKILL.md"
REFERENCES = PRESENT_ROOT / "references"


class PresentSkillMdTests(unittest.TestCase):
    def test_frontmatter_valid(self):
        fm = frontmatter(SKILL.read_text(encoding="utf-8"))
        self.assertEqual(fm["name"], "present")
        self.assertEqual(fm["name"], PRESENT_ROOT.name)
        self.assertTrue(1 <= len(fm["description"]) <= 1024, len(fm["description"]))
        self.assertTrue(1 <= len(fm.get("compatibility", "")) <= 500)
        self.assertEqual(fm.get("license"), "Apache-2.0")
        self.assertIsInstance(fm.get("metadata"), dict)
        for v in fm["metadata"].values():
            self.assertRegex(v, r'^".*"$', "metadata values must be strings (quoted)")
        self.assertEqual(fm["metadata"]["version"], '"0.1.0"')
        self.assertEqual(fm["metadata"]["author"], '"WebStoating"')

    def test_frontmatter_scalars_are_yaml_safe(self):
        block = re.match(r"^---\n(.*?)\n---\n", SKILL.read_text(encoding="utf-8"), re.S).group(1)
        for line in block.splitlines():
            if re.match(r"^\S[^:]*: ", line):
                value = line.split(": ", 1)[1]
                if ": " in value or " #" in value:
                    self.assertRegex(value, r'^".*"$', f"quote this value: {line[:60]}")

    def test_under_500_lines(self):
        self.assertLess(len(SKILL.read_text(encoding="utf-8").splitlines()), 500)

    def test_referenced_files_exist(self):
        text = SKILL.read_text(encoding="utf-8")
        refs = set(re.findall(r"\b((?:references|scripts|assets)/[\w./-]+\.(?:md|py|json))", text))
        expected = {"scripts/check_tools.py", "scripts/settings.py", "scripts/deck.py",
                    "scripts/setup_project.py", "scripts/verify.py",
                    "references/settings.md", "references/slides-and-narration.md",
                    "references/remotion-template.md"}
        self.assertTrue(expected <= refs, expected - refs)
        for r in refs:
            self.assertTrue((PRESENT_ROOT / r).is_file(), r)

    def test_agent_neutral(self):
        for p in [SKILL, *sorted(REFERENCES.glob("*.md"))]:
            text = p.read_text(encoding="utf-8")
            for term in AGENT_SPECIFIC:
                self.assertNotIn(term, text, f"{p.name} names an agent-specific detail: {term}")

    def test_required_strings(self):
        text = SKILL.read_text(encoding="utf-8")
        for s in ("@elevenlabs/cli@1.11.0", "--license-key=free-license", "REMOTION_LICENSE_KEY",
                  "--public-dir", "npx skills add remotion-dev/skills", "npx skills add elevenlabs/skills",
                  "PRESENTATION"):
            self.assertIn(s, text)

    def test_tts_writes_part_file_then_renames(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn('--output "<path>.part"', text)

    def test_env_path_is_quoted(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn('. "<root>/.env"', text)
        self.assertNotIn(". <root>/.env", text)

    def test_slides_and_narration_rules(self):
        text = (REFERENCES / "slides-and-narration.md").read_text(encoding="utf-8")
        for s in ("only what the input says", "150 words", "square brackets"):
            self.assertIn(s, text)


if __name__ == "__main__":
    unittest.main()
