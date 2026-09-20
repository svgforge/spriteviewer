"""Tests for parsing and rendering SVG sprites."""

import pytest

from spriteviewer.icon_store import IconStore, has_resvg, resolve_renderer

SPRITE = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <symbol id="icon-a" viewBox="0 0 24 24">
    <rect width="24" height="24" fill="#000000"/>
  </symbol>
  <symbol id="icon-b" viewBox="0 0 10 10">
    <circle cx="5" cy="5" r="5" fill="#ff0000"/>
  </symbol>
  <symbol>
    <rect width="1" height="1"/>
  </symbol>
</svg>
"""


def test_extract_uses_symbol_ids_in_order():
    store = IconStore(xml=SPRITE)

    assert [icon.id for icon in store.icons] == ["icon-a", "icon-b"]


def test_extract_skips_symbols_without_id():
    store = IconStore(xml=SPRITE)

    assert all(icon.id for icon in store.icons)


def test_each_icon_is_a_standalone_svg_document():
    store = IconStore(xml=SPRITE)

    for icon in store.icons:
        assert icon.svg.startswith("<svg")
        assert "viewBox=" in icon.svg


def test_render_returns_image_of_requested_size(qapp):
    store = IconStore(xml=SPRITE, renderer="qtsvg")

    image = store.render(store.icons[0], 32)

    assert not image.isNull()
    assert image.width() == 32
    assert image.height() == 32


def test_resolve_renderer_qtsvg():
    assert resolve_renderer("qtsvg") == "qtsvg"


def test_default_renderer_is_qtsvg():
    assert IconStore(xml=SPRITE).renderer == "qtsvg"


def test_set_renderer_switches_backend():
    store = IconStore(xml=SPRITE)

    store.set_renderer("qtsvg")

    assert store.renderer == "qtsvg"


def test_set_renderer_unknown_raises():
    store = IconStore(xml=SPRITE)

    with pytest.raises(ValueError):
        store.set_renderer("nope")


@pytest.mark.skipif(not has_resvg(), reason="resvg-py is not installed")
def test_set_renderer_to_resvg():
    store = IconStore(xml=SPRITE)

    store.set_renderer("resvg")

    assert store.renderer == "resvg"


def test_resolve_renderer_auto_picks_available_backend():
    assert resolve_renderer("auto") == ("resvg" if has_resvg() else "qtsvg")


def test_resolve_renderer_unknown_raises():
    with pytest.raises(ValueError):
        resolve_renderer("nope")


@pytest.mark.skipif(has_resvg(), reason="resvg-py is installed")
def test_explicit_resvg_without_package_raises():
    with pytest.raises(RuntimeError):
        resolve_renderer("resvg")
