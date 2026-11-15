"""Keep printing from crashing on consoles that cannot encode a character."""
import sys


def safe_stdout() -> None:
    """On Windows, piped output uses the ANSI code page with strict errors, and `python3 -I` ignores
    PYTHONIOENCODING, so a path or symbol outside the code page would raise UnicodeEncodeError."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass
