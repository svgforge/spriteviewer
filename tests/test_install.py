"""Tests for pure installer helpers."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from install import _ps_quote, _windows_shortcut_script


def test_ps_quote_escapes_single_quotes():
    assert _ps_quote("O'Hara") == "O''Hara"


def test_windows_shortcut_script_escapes_paths():
    shortcut = Path(
        r"C:\Users\O'Hara\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Sprite Viewer.lnk"
    )
    executable = Path(
        r"C:\Users\O'Hara\AppData\Local\spriteviewer\venv\Scripts\spriteviewer.exe"
    )

    script = _windows_shortcut_script(shortcut, executable)

    assert "O''Hara" in script
    assert "O'Hara" not in script.replace("O''Hara", "")
    assert "$sc.Save()" in script
