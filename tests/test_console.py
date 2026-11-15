import io
import sys
import unittest

import tests._path  # noqa: F401  (puts scripts/ on sys.path)

from vts_lib.console import safe_stdout


class ConsoleTests(unittest.TestCase):
    def test_unencodable_output_does_not_crash(self):
        """Windows pipes use the ANSI code page with strict errors; -I ignores PYTHONIOENCODING."""
        saved = sys.stdout
        raw = io.BytesIO()
        sys.stdout = io.TextIOWrapper(raw, encoding="ascii", errors="strict")
        try:
            safe_stdout()
            print("path: C:/Users/\u4fa1\u683c/d\u00e9mo \u2013 ok")
            sys.stdout.flush()
            written = raw.getvalue()
        finally:
            sys.stdout = saved
        self.assertIn(b"ok", written)


if __name__ == "__main__":
    unittest.main()
