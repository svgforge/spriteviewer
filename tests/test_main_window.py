"""Tests for the main window's renderer switch."""

import pytest
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QLabel, QStyleFactory

from spriteviewer.icon_store import IconStore, has_resvg
from spriteviewer.main_window import DARK_BACKGROUND, MainWindow

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
        assert label.text() == "No icons found in SVG sprite"
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


def test_selected_item_fills_the_whole_cell(qapp):
    """Selection covers the whole cell with a 2px gap, on every style."""
    window = MainWindow(IconStore(xml=SPRITE), initial_size=64)
    try:
        window._grid.setCurrentItem(window._grid.item(0))
        qapp.processEvents()
        image = window._grid.grab().toImage()
        cell = window._grid.visualItemRect(window._grid.item(0))
        highlight = qapp.palette().highlight().color()

        def is_highlight(color) -> bool:
            return (
                abs(color.red() - highlight.red()) <= 8
                and abs(color.green() - highlight.green()) <= 8
                and abs(color.blue() - highlight.blue()) <= 8
            )

        # Sample in the left margin: inside the selection, outside the icon and
        # rounded corners.
        x = cell.x() + 5
        assert not is_highlight(image.pixelColor(x, cell.y()))
        assert not is_highlight(image.pixelColor(x, cell.y() + 1))
        top = cell.y() + 6
        bottom = cell.y() + cell.height() - 6
        matching = sum(1 for y in range(top, bottom) if is_highlight(image.pixelColor(x, y)))
        assert matching >= (bottom - top) * 0.97
    finally:
        _close(window)


@pytest.mark.parametrize("style_name", ["fusion", "windows"])
def test_selection_looks_the_same_across_styles_and_palettes(qapp, style_name):
    """Selection (rounded, 2px inset) is painted itself and must not depend
    on which QStyle or colour scheme the platform provides."""
    old_style = qapp.style().objectName()
    old_palette = QPalette(qapp.palette())
    try:
        style = QStyleFactory.create(style_name)
        if style is None:
            pytest.skip(f"style {style_name} unavailable")
        qapp.setStyle(style)

        dark = QPalette(old_palette)
        dark.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        dark.setColor(QPalette.ColorRole.Base, QColor(20, 20, 20))
        dark.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        qapp.setPalette(dark)

        window = MainWindow(IconStore(xml=SPRITE), initial_size=64)
        try:
            window._grid.setCurrentItem(window._grid.item(0))
            qapp.processEvents()
            image = window._grid.grab().toImage()
            cell = window._grid.visualItemRect(window._grid.item(0))
            highlight = qapp.palette().highlight().color()

            def is_highlight(color) -> bool:
                return (
                    abs(color.red() - highlight.red()) <= 8
                    and abs(color.green() - highlight.green()) <= 8
                    and abs(color.blue() - highlight.blue()) <= 8
                )

            # Sample in the left margin: inside the selection, outside the icon
            # and rounded corners.
            x = cell.x() + 5
            assert not is_highlight(image.pixelColor(x, cell.y()))
            assert not is_highlight(image.pixelColor(x, cell.y() + 1))
            top = cell.y() + 6
            bottom = cell.y() + cell.height() - 6
            matching = sum(
                1 for y in range(top, bottom) if is_highlight(image.pixelColor(x, y))
            )
            assert matching >= (bottom - top) * 0.97
        finally:
            _close(window)
    finally:
        qapp.setPalette(old_palette)
        restore = QStyleFactory.create(old_style)
        if restore is not None:
            qapp.setStyle(restore)


def test_dark_mode_toggles_grid_stylesheet(qapp):
    window = MainWindow(IconStore(xml=SPRITE))
    try:
        assert window._grid.styleSheet() == ""
        window._set_dark_mode(True)
        assert DARK_BACKGROUND in window._grid.styleSheet()
        window._set_dark_mode(False)
        assert window._grid.styleSheet() == ""
    finally:
        _close(window)


def test_load_sprite_updates_title_status_and_renderer_controls(qapp):
    window = MainWindow(IconStore(xml=SPRITE))
    try:
        window.load_sprite(IconStore(xml=EMPTY_SPRITE), sprite_path=None)
        assert window.windowTitle() == "SVG Sprite Viewer"
        assert "0 icons loaded" in window.statusBar().currentMessage()

        window.load_sprite(IconStore(xml=SPRITE))
        assert "1 icons loaded" in window.statusBar().currentMessage()
        assert window._renderer_label.text().startswith("Renderer:")
    finally:
        _close(window)


def test_copy_id_and_svg_to_clipboard(qapp):
    window = MainWindow(IconStore(xml=SPRITE))
    try:
        icon = window._icons[0]
        window._copy_ids([icon])
        assert qapp.clipboard().text() == icon.id

        window._copy_svg([icon])
        assert qapp.clipboard().text() == icon.svg
    finally:
        _close(window)


def test_close_event_with_running_loader(qapp):
    window = MainWindow(IconStore(xml=SPRITE))
    window.show()
    qapp.processEvents()
    window.close()
    qapp.processEvents()
    assert window._loader is not None
