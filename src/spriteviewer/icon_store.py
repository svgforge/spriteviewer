"""Parsing of an SVG sprite file into individual icons and their rendering."""

from __future__ import annotations

import gzip
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

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
        root = ET.fromstring(xml)
        default_viewbox = root.get("viewBox", "0 0 64 64")
        icons = []
        for symbol in root.iter(f"{{{SVG_NS}}}symbol"):
            icon_id = symbol.get("id")
            if not icon_id:
                continue
            viewbox = self._parse_viewbox(symbol.get("viewBox", default_viewbox))
            icons.append(Icon(id=icon_id, svg=self._to_document(symbol, viewbox)))
        return icons

    @staticmethod
    def _parse_viewbox(value: str) -> tuple[float, float, float, float]:
        x, y, w, h = (float(v) for v in value.split())
        return x, y, w, h

    @staticmethod
    def _to_document(symbol, viewbox) -> str:
        """Wrap a symbol into a standalone SVG document.

        Each symbol is self-contained (gradients, clip paths etc. live inside
        it), so copying its child elements is enough for a correct render.
        """
        x, y, w, h = viewbox
        svg = ET.Element(
            f"{{{SVG_NS}}}svg",
            {
                "viewBox": f"{x} {y} {w} {h}",
                "width": f"{w}",
                "height": f"{h}",
            },
        )
        for child in symbol:
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
