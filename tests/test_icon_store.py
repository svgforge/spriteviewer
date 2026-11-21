"""Tests for parsing and rendering SVG sprites."""

import gzip
import zipfile

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


def test_reads_gzip_compressed_sprite(tmp_path):
    sprite = tmp_path / "sprite.svg.gz"
    sprite.write_bytes(gzip.compress(SPRITE.encode("utf-8")))

    store = IconStore(sprite)

    assert [icon.id for icon in store.icons] == ["icon-a", "icon-b"]


def test_reads_svgz_sprite(tmp_path):
    sprite = tmp_path / "sprite.svgz"
    sprite.write_bytes(gzip.compress(SPRITE.encode("utf-8")))

    store = IconStore(sprite)

    assert [icon.id for icon in store.icons] == ["icon-a", "icon-b"]


def test_reads_zip_containing_single_svg(tmp_path):
    sprite = tmp_path / "sprite.svg.zip"
    with zipfile.ZipFile(sprite, "w") as archive:
        archive.writestr("sprite.svg", SPRITE)

    store = IconStore(sprite)

    assert [icon.id for icon in store.icons] == ["icon-a", "icon-b"]


def test_reads_zip_containing_nested_single_svg(tmp_path):
    sprite = tmp_path / "sprite.svg.zip"
    with zipfile.ZipFile(sprite, "w") as archive:
        archive.writestr("icons/sprite.svg", SPRITE)

    store = IconStore(sprite)

    assert [icon.id for icon in store.icons] == ["icon-a", "icon-b"]


def test_zip_without_svg_raises(tmp_path):
    sprite = tmp_path / "sprite.svg.zip"
    with zipfile.ZipFile(sprite, "w") as archive:
        archive.writestr("readme.txt", "no svg here")

    with pytest.raises(ValueError):
        IconStore(sprite)


def test_zip_with_multiple_svgs_raises(tmp_path):
    sprite = tmp_path / "sprite.svg.zip"
    with zipfile.ZipFile(sprite, "w") as archive:
        archive.writestr("one.svg", SPRITE)
        archive.writestr("two.svg", SPRITE)

    with pytest.raises(ValueError):
        IconStore(sprite)


def test_reads_plain_svg_file(tmp_path):
    sprite = tmp_path / "sprite.svg"
    sprite.write_text(SPRITE, encoding="utf-8")

    store = IconStore(sprite)

    assert [icon.id for icon in store.icons] == ["icon-a", "icon-b"]


def test_parse_viewbox_accepts_commas():
    sprite = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <symbol id="icon-a" viewBox="0,0,24,24"><rect width="24" height="24"/></symbol>
</svg>
"""
    store = IconStore(xml=sprite)

    assert store.icons[0].svg.startswith("<svg")
    assert 'viewBox="0.0 0.0 24.0 24.0"' in store.icons[0].svg


def test_parse_viewbox_accepts_mixed_commas_and_whitespace():
    sprite = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <symbol id="icon-a" viewBox="0, 0, 24, 24"><rect width="24" height="24"/></symbol>
</svg>
"""
    store = IconStore(xml=sprite)

    assert 'viewBox="0.0 0.0 24.0 24.0"' in store.icons[0].svg


def test_symbol_without_viewbox_falls_back_to_root_viewbox():
    sprite = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <symbol id="icon-a"><rect width="16" height="16"/></symbol>
</svg>
"""
    store = IconStore(xml=sprite)

    assert 'viewBox="0.0 0.0 16.0 16.0"' in store.icons[0].svg


def test_renderer_name():
    store = IconStore(xml=SPRITE, renderer="qtsvg")

    assert store.renderer_name() == "QtSvg (SVG Tiny)"


def test_path_and_xml_none_raise_clear_error():
    with pytest.raises(ValueError, match="either 'path' or 'xml' must be provided"):
        IconStore()


def test_rejects_xml_entity_expansion():
    xml = """\
<?xml version="1.0"?>
<!DOCTYPE svg [
  <!ENTITY boom "boom">
]>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">
  <symbol id="a" viewBox="0 0 1 1"><rect width="1" height="1"/></symbol>
  <text>&boom;</text>
</svg>
"""
    with pytest.raises(Exception) as exc_info:
        IconStore(xml=xml)

    assert "EntitiesForbidden" in type(exc_info.value).__name__
