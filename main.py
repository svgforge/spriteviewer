#!/usr/bin/env python3
"""Development entry point (identical to the installed `spriteviewer` command).

Bootstraps the ``src/`` layout onto ``sys.path`` so the app also works
straight from a fresh checkout without an install step.

If a project-local ``.venv`` exists, the script re-executes itself with that
interpreter first. The virtualenv provides the full-standard ``resvg`` glyph
renderer, so icons are drawn with the complete SVG feature set (gradients,
filters, …) instead of silently degrading to the QtSvg fallback.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _venv_python() -> Path | None:
    """Interpreter of the project-local virtualenv, if one exists."""
    for candidate in (
        PROJECT_ROOT / ".venv" / "bin" / "python",
        PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
    ):
        if candidate.is_file():
            return candidate
    return None


def _reexec_in_venv() -> None:
    """Replace this process with ``.venv``'s interpreter (once, if present)."""
    if os.environ.get("_SPRITEVIEWER_VENV") == "1":
        return  # already re-executed; never loop
    python = _venv_python()
    if python is None:
        return  # no virtualenv: fall back to the current interpreter
    if Path(sys.prefix).resolve() == (PROJECT_ROOT / ".venv").resolve():
        return  # already running inside the virtualenv
    os.environ["_SPRITEVIEWER_VENV"] = "1"
    os.execv(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]])


def main() -> int:
    from spriteviewer.app import main as app_main

    return app_main()


if __name__ == "__main__":
    _reexec_in_venv()
    raise SystemExit(main())
