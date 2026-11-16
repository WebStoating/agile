import tempfile
import unittest
from pathlib import Path

from tests import _path  # noqa: F401
from pr_lib.envfile import lookup, parse_dotenv, source


class EnvFileTests(unittest.TestCase):
    def test_parse_forms(self):
        text = "# c\n\nexport A=1\nB=\"two words\"\nC='x#y'\nD=val # trailing\nE=\n"
        self.assertEqual(parse_dotenv(text),
                         {"A": "1", "B": "two words", "C": "x#y", "D": "val", "E": ""})

    def test_quoted_value_with_trailing_comment(self):
        text = "B=\"x y\" # c\nC='z' # c\nD=\"a#b\"\nE=\"unterminated\n"
        self.assertEqual(parse_dotenv(text),
                         {"B": "x y", "C": "z", "D": "a#b", "E": "\"unterminated"})

    def test_embedded_quote_keeps_outer_stripping(self):
        self.assertEqual(parse_dotenv('K="pa"ss"\n'), {"K": 'pa"ss'})

    def test_lookup_order(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / ".env"
            f.write_text("K=fromfile\nEMPTY=\n", encoding="utf-8")
            self.assertEqual(lookup("K", {"K": "fromenv"}, f), "fromenv")
            self.assertEqual(lookup("K", {"K": ""}, f), "fromfile")
            self.assertIsNone(lookup("EMPTY", {}, f))
            self.assertIsNone(lookup("K", {}, Path(d) / "missing"))
            self.assertIsNone(lookup("K", {}, None))

    def test_source(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / ".env"
            f.write_text("K=v\nEMPTY=\n", encoding="utf-8")
            self.assertEqual(source("K", {"K": "e"}, f), "env")
            self.assertEqual(source("K", {"K": ""}, f), ".env")
            self.assertIsNone(source("EMPTY", {}, f))
            self.assertIsNone(source("K", {}, None))


if __name__ == "__main__":
    unittest.main()
