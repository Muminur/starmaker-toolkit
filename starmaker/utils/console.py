"""Shared Rich console with forced UTF-8 output for Windows compatibility."""

from __future__ import annotations

import io
import sys

from rich.console import Console


def _make_console() -> Console:
    """Create a Rich Console with UTF-8 encoding on Windows.

    Avoids replacing ``sys.stdout`` at import time (which breaks pytest
    capture) by passing a UTF-8 ``TextIOWrapper`` directly to ``Console`` only
    when needed.

    If ``sys.stdout`` has no usable ``.buffer`` (for example under pytest's
    output capture, where stdout is replaced with a non-binary object), the
    wrapper is skipped and a default :class:`~rich.console.Console` is returned
    so console creation never fails.

    Returns:
        A configured Rich console.
    """
    if sys.platform == "win32":
        buffer = getattr(sys.stdout, "buffer", None)
        if buffer is not None:
            try:
                utf8_stdout = io.TextIOWrapper(
                    buffer, encoding="utf-8", errors="replace"
                )
                return Console(file=utf8_stdout, highlight=False)
            except (AttributeError, ValueError, io.UnsupportedOperation):
                # stdout has no/closed binary buffer (e.g. pytest capture);
                # fall back to a plain console rather than failing.
                pass
    return Console()


console = _make_console()
