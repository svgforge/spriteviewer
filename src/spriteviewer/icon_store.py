"""Parsing of an SVG sprite file into individual icons and their rendering."""

from __future__ import annotations

import copy
import gzip
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

from defusedxml.ElementTree import fromstring as _safe_fromstring
from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

try:  # full SVG 1.1 support (markers, filters, …); falls back to QtSvg below
    from resvg_py import svg_to_bytes as _resvg_svg_to_bytes
except ImportError:
    _resvg_svg_to_bytes = None


RENDERER_CHOICES = ("qtsvg", "resvg", "auto")

_RENDERER_LABELS = {
    "resvg": "resvg (full SVG 1.1)",
    "qtsvg": "QtSvg (SVG Tiny)",
}


def resolve_renderer(choice: str = "qtsvg") -> str:
    """Map a renderer choice to the backend that will actually be used."""
    if choice == "resvg":
        if _resvg_svg_to_bytes is None:
            raise RuntimeError("resvg-py is not installed; install it or use 'qtsvg'")
        return "resvg"
    if choice == "qtsvg":
        return "qtsvg"
    if choice == "auto":
        return "resvg" if _resvg_svg_to_bytes is not None else "qtsvg"
    raise ValueError(f"unknown renderer: {choice!r}")


def has_resvg() -> bool:
    return _resvg_svg_to_bytes is not None


@dataclass(frozen=True)
class Icon:
    """A single icon extracted from the SVG sprite, ready to be rendered."""

    id: str
    svg: str  # self-contained SVG document for this icon


def read_sprite_text(path: str | Path) -> str:
    """Read an SVG sprite, transparently decompressing .svgz/.svg.gz/.zip."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".svgz", ".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return handle.read()
    if suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            members = [
                name for name in archive.namelist() if name.lower().endswith(".svg")
            ]
            if not members:
                raise ValueError(f"'{path}' contains no .svg file")
            if len(members) > 1:
                raise ValueError(
                    f"'{path}' contains {len(members)} .svg files; "
                    "extract the sprite first"
                )
            return archive.read(members[0]).decode("utf-8")
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class IconStore:
    """Loads an SVG sprite file and exposes its icons."""

    def __init__(
        self,
        path: str | Path | None = None,
        xml: str | None = None,
        renderer: str = "qtsvg",
    ):
        self._renderer = resolve_renderer(renderer)
        if xml is None:
            if path is None:
                raise ValueError("either 'path' or 'xml' must be provided")
            xml = read_sprite_text(path)
        self.icons = self._extract(xml)

    @property
    def renderer(self) -> str:
        """Backend actually used for rendering ('resvg' or 'qtsvg')."""
        return self._renderer

    def set_renderer(self, choice: str) -> None:
        """Switch the rendering backend at runtime ('qtsvg', 'resvg' or 'auto')."""
        self._renderer = resolve_renderer(choice)

    def renderer_name(self) -> str:
        """Human-readable name of the active backend."""
        return _RENDERER_LABELS[self._renderer]

    def _extract(self, xml: str) -> list[Icon]:
        root = _safe_fromstring(xml)
        default_viewbox = root.get("viewBox", "0 0 64 64")

        views = self._extract_views(root)
        if views:
            return views

        symbols = self._extract_symbols(root, default_viewbox)
        if symbols:
            return symbols

        defs_icons = self._extract_defs(root, default_viewbox)
        if defs_icons:
            return defs_icons

        return self._extract_stack(root, default_viewbox)

    def _extract_views(self, root) -> list[Icon]:
        icons = []
        for view in root.iter(f"{{{SVG_NS}}}view"):
            icon_id = view.get("id")
            viewbox = view.get("viewBox")
            if not icon_id or not viewbox:
                continue
            icons.append(Icon(id=icon_id, svg=self._view_document(root, viewbox)))
        return icons

    @staticmethod
    def _view_document(root, viewbox: str) -> str:
        """Crop the sprite to a <view> region by overriding the root viewBox."""
        x, y, w, h = IconStore._parse_viewbox(viewbox)
        svg = copy.deepcopy(root)
        svg.set("viewBox", f"{x} {y} {w} {h}")
        svg.set("width", f"{w}")
        svg.set("height", f"{h}")
        return ET.tostring(svg, encoding="unicode")

    def _extract_symbols(self, root, default_viewbox: str) -> list[Icon]:
        icons = []
        for symbol in root.iter(f"{{{SVG_NS}}}symbol"):
            icon_id = symbol.get("id")
            if not icon_id:
                continue
            viewbox = self._parse_viewbox(symbol.get("viewBox", default_viewbox))
            icons.append(Icon(id=icon_id, svg=self._symbol_document(symbol, viewbox)))
        return icons

    def _extract_defs(self, root, default_viewbox: str) -> list[Icon]:
        icons = []
        for defs in root.iter(f"{{{SVG_NS}}}defs"):
            for child in list(defs):
                icon_id = child.get("id")
                if not icon_id:
                    continue
                if child.tag not in (
                    f"{{{SVG_NS}}}svg",
                    f"{{{SVG_NS}}}symbol",
                    f"{{{SVG_NS}}}g",
                ):
                    continue
                icons.append(
                    Icon(id=icon_id, svg=self._element_document(child, default_viewbox))
                )
        return icons

    def _extract_stack(self, root, default_viewbox: str) -> list[Icon]:
        icons = []
        for child in list(root):
            icon_id = child.get("id")
            if not icon_id:
                continue
            if child.tag != f"{{{SVG_NS}}}svg":
                continue
            icons.append(
                Icon(id=icon_id, svg=self._element_document(child, default_viewbox))
            )
        return icons

    @staticmethod
    def _parse_viewbox(value: str) -> tuple[float, float, float, float]:
        parts = value.replace(",", " ").split()
        if len(parts) != 4:
            raise ValueError(f"invalid viewBox: {value!r}")
        x, y, w, h = (float(v) for v in parts)
        return x, y, w, h

    @staticmethod
    def _symbol_document(symbol, viewbox) -> str:
        """Wrap a symbol into a standalone SVG document."""
        x, y, w, h = viewbox
        svg = ET.Element(
            f"{{{SVG_NS}}}svg",
            {
                "viewBox": f"{x} {y} {w} {h}",
                "width": f"{w}",
                "height": f"{h}",
            },
        )
        for child in copy.deepcopy(symbol):
            svg.append(child)
        return ET.tostring(svg, encoding="unicode")

    @staticmethod
    def _element_document(element, default_viewbox: str) -> str:
        """Serialize an SVG shape element as a standalone SVG document."""
        element = copy.deepcopy(element)
        if element.tag == f"{{{SVG_NS}}}svg":
            viewbox = element.get("viewBox", default_viewbox)
            x, y, w, h = IconStore._parse_viewbox(viewbox)
            element.set("viewBox", f"{x} {y} {w} {h}")
            element.set("width", f"{w}")
            element.set("height", f"{h}")
            return ET.tostring(element, encoding="unicode")

        if element.tag == f"{{{SVG_NS}}}symbol":
            viewbox = IconStore._parse_viewbox(element.get("viewBox", default_viewbox))
            return IconStore._symbol_document(element, viewbox)

        viewbox = IconStore._parse_viewbox(element.get("viewBox", default_viewbox))
        return IconStore._to_document(element, viewbox)

    @staticmethod
    def _to_document(element, viewbox) -> str:
        """Wrap an element's children into a standalone SVG document."""
        x, y, w, h = viewbox
        svg = ET.Element(
            f"{{{SVG_NS}}}svg",
            {
                "viewBox": f"{x} {y} {w} {h}",
                "width": f"{w}",
                "height": f"{h}",
            },
        )
        for child in copy.deepcopy(element):
            svg.append(child)
        return ET.tostring(svg, encoding="unicode")

    def render(self, icon: Icon, size: int) -> QImage:
        """Render an icon into a transparent QImage of the given edge size."""
        if self._renderer == "resvg":
            try:
                png = _resvg_svg_to_bytes(svg_string=icon.svg, width=size, height=size)
                image = QImage()
                if png and image.loadFromData(png):
                    return image
            except Exception:  # noqa: BLE001, S110 - fall back per icon
                pass  # one bad glyph must not blank the whole view
        return _render_qtsvg(icon.svg, size)


def _render_qtsvg(xml: str, size: int) -> QImage:
    """Qt fallback renderer (SVG Tiny profile; used without resvg-py)."""
    renderer = QSvgRenderer(QByteArray(xml.encode("utf-8")))
    image = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    renderer.render(painter, QRectF(0.0, 0.0, float(size), float(size)))
    painter.end()
    return image
