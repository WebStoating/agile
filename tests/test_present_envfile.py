import tempfile
import unittest
from pathlib import Path

from tests import _path  # noqa: F401
from pr_lib.envfile import lookup, parse_dotenv


class EnvFileTests(unittest.TestCase):
    def test_parse_forms(self):
        text = "# c\n\nexport A=1\nB=\"two words\"\nC='x#y'\nD=val # trailing\nE=\n"
        self.assertEqual(parse_dotenv(text),
                         {"A": "1", "B": "two words", "C": "x#y", "D": "val", "E": ""})

    def test_lookup_order(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / ".env"
            f.write_text("K=fromfile\nEMPTY=\n", encoding="utf-8")
            self.assertEqual(lookup("K", {"K": "fromenv"}, f), "fromenv")
            self.assertEqual(lookup("K", {"K": ""}, f), "fromfile")
            self.assertIsNone(lookup("EMPTY", {}, f))
            self.assertIsNone(lookup("K", {}, Path(d) / "missing"))
            self.assertIsNone(lookup("K", {}, None))


if __name__ == "__main__":
    unittest.main()
