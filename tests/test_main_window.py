"""Tests for the main window's renderer switch."""

import pytest
from PySide6.QtWidgets import QLabel

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


EMPTY_SPRITE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 8">'
    '<rect width="8" height="8"/>'
    "</svg>"
)


def test_sprite_without_symbols_shows_empty_state_message(qapp):
    window = MainWindow(IconStore(xml=EMPTY_SPRITE))
    try:
        assert window._stack.currentIndex() == 1
        label = window._empty_state.findChild(QLabel)
        assert label is not None
        assert label.text() == "no valid svg file with symbols"
    finally:
        _close(window)


def test_loading_sprite_with_symbols_after_empty_returns_to_grid(qapp):
    window = MainWindow(IconStore(xml=EMPTY_SPRITE))
    try:
        assert window._stack.currentIndex() == 1
        window.load_sprite(IconStore(xml=SPRITE))
        assert window._stack.currentIndex() == 0
    finally:
        _close(window)
