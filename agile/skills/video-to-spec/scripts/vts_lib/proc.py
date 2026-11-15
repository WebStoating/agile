"""Run external tools safely: argv lists only, never a shell."""
import shutil
import subprocess
from typing import List, Optional


class ToolError(Exception):
    """An external tool is missing or failed."""


def run(argv: List[str], timeout: Optional[float] = None) -> "subprocess.CompletedProcess[str]":
    exe = shutil.which(argv[0])
    if exe is None:
        raise ToolError(f"{argv[0]} not found on PATH")
    try:
        return subprocess.run([exe, *argv[1:]], capture_output=True, text=True, errors="replace",
                              timeout=timeout)
    except OSError as e:
        raise ToolError(f"could not run {argv[0]}: {e}") from e
    except subprocess.TimeoutExpired as e:
        raise ToolError(f"{argv[0]} timed out after {timeout}s") from e


def run_bytes(argv: List[str], timeout: Optional[float] = None) -> "subprocess.CompletedProcess[bytes]":
    """Like run(), but stdout/stderr stay bytes (for raw video frames)."""
    exe = shutil.which(argv[0])
    if exe is None:
        raise ToolError(f"{argv[0]} not found on PATH")
    try:
        return subprocess.run([exe, *argv[1:]], capture_output=True, timeout=timeout)
    except OSError as e:
        raise ToolError(f"could not run {argv[0]}: {e}") from e
    except subprocess.TimeoutExpired as e:
        raise ToolError(f"{argv[0]} timed out after {timeout}s") from e
