"""Tests for the GNU-getopt command line interface."""

import pytest

from spriteviewer import __version__
from spriteviewer.app import parse_args
from spriteviewer.main_window import DEFAULT_SIZE


def test_defaults():
    sprite, size, renderer = parse_args([])

    assert sprite.name == "icons.svg"
    assert size == DEFAULT_SIZE
    assert renderer == "qtsvg"


@pytest.mark.parametrize(
    "argv", [["-S", "32"], ["-S32"], ["--size", "32"], ["--size=32"]]
)
def test_size_accepts_all_getopt_forms(argv):
    assert parse_args(argv)[1] == 32


@pytest.mark.parametrize(
    "argv",
    [["-R", "qtsvg"], ["-Rqtsvg"], ["--renderer", "qtsvg"], ["--renderer=qtsvg"]],
)
def test_renderer_accepts_all_getopt_forms(argv):
    assert parse_args(argv)[2] == "qtsvg"


def test_sprite_is_positional_and_may_interleave():
    sprite, size, _ = parse_args(["--size", "64", "sprite.svg"])

    assert sprite.name == "sprite.svg"
    assert size == 64


def test_invalid_size_exits_with_code_2():
    with pytest.raises(SystemExit) as exit_info:
        parse_args(["--size", "7"])

    assert exit_info.value.code == 2


def test_invalid_renderer_exits_with_code_2():
    with pytest.raises(SystemExit) as exit_info:
        parse_args(["--renderer", "nope"])

    assert exit_info.value.code == 2


def test_too_many_operands_exits_with_code_2():
    with pytest.raises(SystemExit) as exit_info:
        parse_args(["one.svg", "two.svg"])

    assert exit_info.value.code == 2


def test_help_exits_with_code_0(capsys):
    with pytest.raises(SystemExit) as exit_info:
        parse_args(["--help"])

    assert exit_info.value.code == 0
    assert "usage:" in capsys.readouterr().out


@pytest.mark.parametrize("argv", [["-V"], ["--version"]])
def test_version_exits_with_code_0(argv, capsys):
    with pytest.raises(SystemExit) as exit_info:
        parse_args(argv)

    assert exit_info.value.code == 0
    assert __version__ in capsys.readouterr().out
