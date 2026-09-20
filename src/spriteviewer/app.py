"""Installed entry point for the Sprite Viewer (`spriteviewer` command).

Shares all logic with the development script `main.py`; this module is used
by the pip-installed console script so the app also works outside the source
tree.
"""

from __future__ import annotations

import getopt
import sys
from importlib import resources
from pathlib import Path
from typing import NoReturn

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from spriteviewer._version import __version__
from spriteviewer.icon_store import RENDERER_CHOICES, IconStore, has_resvg
from spriteviewer.main_window import DEFAULT_SIZE, ICON_SIZES, MainWindow


def _asset(name: str) -> Path:
    """Path of a data file bundled with the package."""
    return Path(resources.files("spriteviewer").joinpath(name))


USAGE = f"""\
usage: {Path(sys.argv[0]).name} [OPTION] [SPRITE]

Display a sprite sheet as an interactive window.

The SPRITE is positional and optional (default: the bundled sprite).

Options:
  -h, --help        show this help and exit
  -V, --version     show the version and exit
  -S, --size N      icon size in pixels; one of {ICON_SIZES}
                    (accepts "-S 32", "-S32", "--size 32" or "--size=32")
  -R, --renderer R  SVG backend: qtsvg (default), resvg or auto
                    (accepts "-R resvg", "-Rresvg", "--renderer resvg")
"""


def _fail(message: str) -> NoReturn:
    print(f"{Path(sys.argv[0]).name}: error: {message}", file=sys.stderr)
    print(
        f"Try '{Path(sys.argv[0]).name} --help' for more information.", file=sys.stderr
    )
    raise SystemExit(2)


def parse_args(argv: list[str]) -> tuple[Path, int, str]:
    # GNU getopt (stdlib `getopt.gnu_getopt`): options and the sprite may
    # interleave, "-S 32", "-S32", "--size 32" and "--size=32" are all
    # equivalent, and "--" ends option parsing. The sprite is purely
    # positional: the first operand (default: the bundled sprite).
    sprite = None
    size = DEFAULT_SIZE
    renderer = "qtsvg"
    try:
        options, operands = getopt.gnu_getopt(
            argv,
            "hS:R:V",
            ["help", "size=", "renderer=", "version"],
        )
    except getopt.GetoptError as error:
        _fail(f"{error} (use --help for usage)")
    for option, value in options:
        if option in ("-h", "--help"):
            print(USAGE)
            raise SystemExit(0)
        if option in ("-V", "--version"):
            print(f"{Path(sys.argv[0]).name} {__version__}")
            raise SystemExit(0)
        if option in ("-S", "--size"):
            try:
                size = int(value)
            except ValueError:
                _fail(f"--size expects an integer, got {value!r}")
            if size not in ICON_SIZES:
                _fail(f"--size must be one of {ICON_SIZES}, got {size}")
        if option in ("-R", "--renderer"):
            if value not in RENDERER_CHOICES:
                _fail(f"--renderer must be one of {RENDERER_CHOICES}, got {value!r}")
            renderer = value
    if operands:
        sprite = operands[0]
    if len(operands) > 1:
        _fail(f"unexpected argument: {operands[1]!r}")
    sprite_path = Path(sprite) if sprite else _asset("icons.svg")
    return sprite_path, size, renderer


def main(argv: list[str] | None = None) -> int:
    sprite_path, size, renderer = parse_args(sys.argv[1:] if argv is None else argv)
    if renderer == "resvg" and not has_resvg():
        _fail("resvg-py is not installed; use '--renderer qtsvg' or install resvg-py")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(_asset("spriteviewer.svg"))))

    store = IconStore(sprite_path, renderer=renderer)
    window = MainWindow(store, initial_size=size, sprite_path=sprite_path)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
