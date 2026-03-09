"""Shared Rich console with forced UTF-8 output for Windows compatibility."""

from __future__ import annotations

import io
import sys

from rich.console import Console

# Force UTF-8 output on Windows to avoid cp1252 encoding errors with Unicode
# characters like checkmarks (✓ ✗), emojis (🚀 ✅ ❌), etc.
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

console = Console()
