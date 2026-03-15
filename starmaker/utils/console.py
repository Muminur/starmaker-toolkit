"""Shared Rich console with forced UTF-8 output for Windows compatibility."""

from __future__ import annotations

import io
import sys

from rich.console import Console


def _make_console() -> Console:
    """Create a Rich Console with UTF-8 encoding on Windows.

    Avoids replacing sys.stdout at import time (which breaks pytest capture)
    by passing a UTF-8 TextIOWrapper directly to Console only when needed.
    """
    if sys.platform == "win32":
        try:
            utf8_stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace"
            )
            return Console(file=utf8_stdout, highlight=False)
        except AttributeError:
            # sys.stdout may not have .buffer in some environments (e.g. pytest capture)
            pass
    return Console()


console = _make_console()
