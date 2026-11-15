import re
import unittest

from tests._path import ROOT

SKILL = ROOT / "SKILL.md"
TEMPLATE = ROOT / "assets" / "specification-template.md"
SPEC_RULES = ROOT / "references" / "spec-writing.md"
SECTIONS = [
    "## 1. Instructions for the implementing agent",
    "## 2. Background and goal",
    "## 3. Scope",
    "## 4. Workflow and functional requirements",
    "## 5. Data, results and reporting",
    "## 6. Execution",
    "## 7. Safety and isolation",
    "## 8. Suggested data model",
    "## 9. Acceptance criteria",
    "## 10. Tests",
    "## 11. Open questions",
    "## 12. Appendix: slides and transcript",
]
AGENT_SPECIFIC = ("Read tool", "Bash tool", "view_image", "TodoWrite", "Claude Code's", "1568")


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "missing frontmatter"
    fm, cur = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^\S[^:]*:", line):
            k, v = line.split(":", 1)
            cur = k.strip()
            fm[cur] = v.strip().strip('"') if v.strip() else {}
        elif cur and isinstance(fm[cur], dict) and line.startswith("  "):
            k, v = line.strip().split(":", 1)
            fm[cur][k.strip()] = v.strip()
    return fm


class SkillMdTests(unittest.TestCase):
    def test_frontmatter_valid(self):
        fm = frontmatter(SKILL.read_text())
        self.assertEqual(fm["name"], ROOT.name)
        self.assertEqual(fm["name"], "video-to-spec")
        self.assertRegex(fm["name"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertLessEqual(len(fm["name"]), 64)
        self.assertTrue(1 <= len(fm["description"]) <= 1024, len(fm["description"]))
        self.assertLessEqual(len(fm.get("compatibility", "")), 500)
        self.assertIsInstance(fm.get("metadata"), dict)
        for v in fm["metadata"].values():
            self.assertRegex(v, r'^".*"$', "metadata values must be strings (quoted)")

    def test_frontmatter_scalars_are_yaml_safe(self):
        """An unquoted value containing ': ' is invalid YAML (strict parsers reject the skill)."""
        block = re.match(r"^---\n(.*?)\n---\n", SKILL.read_text(), re.S).group(1)
        for line in block.splitlines():
            if re.match(r"^\S[^:]*: ", line):
                value = line.split(": ", 1)[1]
                if ": " in value or " #" in value:
                    self.assertRegex(value, r'^".*"$', f"quote this value: {line[:60]}")

    def test_under_500_lines(self):
        self.assertLess(len(SKILL.read_text().splitlines()), 500)

    def test_referenced_files_exist(self):
        refs = set(re.findall(r"\b((?:references|scripts|assets)/[\w./-]+\.(?:md|py))", SKILL.read_text()))
        self.assertTrue({"scripts/check_tools.py", "scripts/transcribe.py", "scripts/extract_slides.py",
                         "references/spec-writing.md", "references/frame-extraction.md",
                         "assets/specification-template.md"} <= refs, refs)
        for r in refs:
            self.assertTrue((ROOT / r).is_file(), r)

    def test_agent_neutral(self):
        for p in [SKILL, *sorted((ROOT / "references").glob("*.md"))]:
            text = p.read_text()
            for term in AGENT_SPECIFIC:
                self.assertNotIn(term, text, f"{p.name} names an agent-specific detail: {term}")

    def test_template_sections(self):
        text = TEMPLATE.read_text()
        positions = [text.find(h) for h in SECTIONS]
        self.assertNotIn(-1, positions, dict(zip(SECTIONS, positions)))
        self.assertEqual(positions, sorted(positions))

    def test_spec_rules_present(self):
        text = SPEC_RULES.read_text()
        for phrase in ("*(added)*", "Not covered in the video", "placeholder", "Do not invent"):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
