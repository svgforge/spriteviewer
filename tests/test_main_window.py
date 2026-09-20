"""Tests for the main window's renderer switch."""

import pytest

from spriteviewer.icon_store import IconStore, has_resvg
from spriteviewer.main_window import MainWindow

SPRITE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 8">'
    '<symbol id="icon-a" viewBox="0 0 8 8"><rect width="8" height="8"/></symbol>'
    "</svg>"
)


def _close(window: MainWindow) -> None:
    window.close()
    if window._loader is not None:
        window._loader.requestInterruption()
        window._loader.wait(2000)


def test_default_renderer_is_qtsvg(qapp):
    window = MainWindow(IconStore(xml=SPRITE))
    try:
        assert window._store.renderer == "qtsvg"
    finally:
        _close(window)


def test_resvg_checkbox_present_only_with_resvg(qapp):
    window = MainWindow(IconStore(xml=SPRITE))
    try:
        assert (window._resvg_check is not None) == has_resvg()
    finally:
        _close(window)


@pytest.mark.skipif(not has_resvg(), reason="resvg-py is not installed")
def test_toggling_checkbox_switches_backend(qapp):
    window = MainWindow(IconStore(xml=SPRITE))
    try:
        window._resvg_check.setChecked(True)
        assert window._store.renderer == "resvg"

        window._resvg_check.setChecked(False)
        assert window._store.renderer == "qtsvg"
    finally:
        _close(window)
