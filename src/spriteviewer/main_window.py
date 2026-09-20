"""Main window with a toolbar (size selector) and a tile view of icons."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6.QtCore import QRect, QSize, Qt, QThread, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolBar,
    QWidget,
)

from spriteviewer.icon_store import Icon, IconStore, has_resvg

ICON_SIZES = (16, 32, 64, 128, 256)
DEFAULT_SIZE = 64
MASTER_SIZE = 256  # rendered once, scaled down by the view to the chosen size
DARK_BACKGROUND = "#2d2d2d"  # background of the icon grid in dark mode


class IconLoader(QThread):
    """Renders icons in the background so the UI stays responsive."""

    rendered = Signal(int, int, QImage)  # generation, index, image

    def __init__(self, store: IconStore, icons, generation: int, parent=None):
        super().__init__(parent)
        self._store = store
        self._icons = list(icons)
        self._generation = generation

    def run(self):
        for index, icon in self._icons:
            if self.isInterruptionRequested():
                return
            self.rendered.emit(
                self._generation, index, self._store.render(icon, MASTER_SIZE)
            )


class _CenteredIconDelegate(QStyledItemDelegate):
    """Paints only the icon, centered, so every cell has equal margins.

    The built-in icon-mode layout reserves space below the icon for a text
    label and top-aligns the icon; drawing it ourselves keeps the icon dead
    center with the same gap on all four sides (and no dead text strip).
    """

    def paint(self, painter, option, index):
        styled = QStyleOptionViewItem(option)
        self.initStyleOption(styled, index)
        styled.text = ""
        styled.icon = QIcon()
        widget = styled.widget
        style = widget.style() if widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, styled, painter, widget)

        icon = index.data(Qt.DecorationRole)
        if icon is None:
            return
        size = option.decorationSize
        rect = QRect(
            option.rect.x() + (option.rect.width() - size.width()) // 2,
            option.rect.y() + (option.rect.height() - size.height()) // 2,
            size.width(),
            size.height(),
        )
        icon.paint(painter, rect)


class MainWindow(QMainWindow):
    def __init__(
        self,
        store: IconStore,
        initial_size: int | None = None,
        sprite_path: Path | None = None,
    ):
        super().__init__()
        self._store = store
        self._icons = store.icons
        self._master_icons: dict[int, QImage] = {}
        self._loader = None
        self._generation = 0
        self._resvg_check: QCheckBox | None = None
        self._sprite_path = sprite_path
        self._current_size = (
            initial_size if initial_size in ICON_SIZES else DEFAULT_SIZE
        )

        self.setWindowTitle(self._title())
        self.resize(900, 700)
        self._build_toolbar()
        self._build_statusbar()
        self._build_icon_grid()
        self._update_status()
        self._start_loading()

    def _build_statusbar(self):
        self._renderer_label = QLabel(f"Renderer: {self._store.renderer_name()}")
        self._renderer_label.setToolTip(
            "resvg renders the full SVG 1.1 spec (gradients, filters, masks),\n"
            "but is noticeably slower. QtSvg (SVG Tiny) is much faster and\n"
            "preferable for simple icons."
        )
        self.statusBar().addPermanentWidget(self._renderer_label)

    def _title(self) -> str:
        suffix = f" - {self._sprite_path.name}" if self._sprite_path else ""
        return f"SVG Sprite Viewer{suffix}"

    def _build_toolbar(self):
        toolbar = QToolBar("Icons")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_button = QPushButton("Open Sprite")
        open_button.setToolTip("Load a different SVG sprite file")
        open_button.clicked.connect(self._open_sprite)
        toolbar.addWidget(open_button)

        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Icon size:  "))
        size_combo = QComboBox()
        for size in ICON_SIZES:
            size_combo.addItem(f"{size} x {size}", size)
        size_combo.setCurrentIndex(ICON_SIZES.index(self._current_size))
        size_combo.currentIndexChanged.connect(self._on_size_changed)
        toolbar.addWidget(size_combo)

        toolbar.addSeparator()
        dark_button = QPushButton("Dark mode")
        dark_button.setCheckable(True)
        dark_button.setToolTip("Switch between the light and dark colour scheme")
        dark_button.toggled.connect(self._set_dark_mode)
        toolbar.addWidget(dark_button)

        if has_resvg():
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            toolbar.addWidget(spacer)

            self._resvg_check = QCheckBox("Full SVG (resvg)")
            self._resvg_check.setToolTip(
                "Render with the full SVG 1.1 renderer (resvg): gradients,\n"
                "filters and masks render exactly, but noticeably slower."
            )
            self._resvg_check.setChecked(self._store.renderer == "resvg")
            self._resvg_check.toggled.connect(self._on_renderer_toggled)
            toolbar.addWidget(self._resvg_check)

    def _on_renderer_toggled(self, enabled: bool):
        self._set_renderer("resvg" if enabled else "qtsvg")

    def _set_renderer(self, choice: str):
        """Switch the backend at runtime and re-render the current sprite."""
        self._store.set_renderer(choice)
        self._sync_renderer_controls()
        self._master_icons = {}
        for row in range(self._grid.count()):
            self._grid.item(row).setIcon(QIcon())
        self._start_loading()

    def _sync_renderer_controls(self):
        """Reflect the store's backend in the status label and the checkbox."""
        self._renderer_label.setText(f"Renderer: {self._store.renderer_name()}")
        if self._resvg_check is not None:
            self._resvg_check.blockSignals(True)
            self._resvg_check.setChecked(self._store.renderer == "resvg")
            self._resvg_check.blockSignals(False)

    def _set_dark_mode(self, enabled: bool):
        """Show the icons on a dark background (icon grid only, nothing else)."""
        self._grid.setStyleSheet(
            f"QListWidget {{ background-color: {DARK_BACKGROUND}; }}" if enabled else ""
        )

    def _on_size_changed(self, index: int):
        self._set_icon_size(ICON_SIZES[index])

    def _build_icon_grid(self):
        grid = QListWidget()
        grid.setViewMode(QListWidget.IconMode)
        grid.setResizeMode(QListWidget.Adjust)
        grid.setMovement(QListWidget.Static)
        grid.setUniformItemSizes(True)
        grid.setWordWrap(False)
        grid.setSelectionMode(QListWidget.ExtendedSelection)
        grid.setItemDelegate(_CenteredIconDelegate(grid))
        grid.setContextMenuPolicy(Qt.CustomContextMenu)
        grid.customContextMenuRequested.connect(self._show_context_menu)
        grid.currentItemChanged.connect(self._update_status)
        grid.itemSelectionChanged.connect(self._update_status)
        self._grid = grid
        self.setCentralWidget(grid)
        self._set_icon_size(self._current_size)
        self._populate_grid()

    def _populate_grid(self):
        self._grid.clear()
        width, height = self._cell_size(self._current_size)
        for icon in self._icons:
            item = QListWidgetItem()
            item.setToolTip(icon.id)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            item.setSizeHint(QSize(width, height))
            self._grid.addItem(item)

    def _cell_size(self, size: int) -> tuple[int, int]:
        """Square cell: icon plus the same small margin on every side."""
        margin = max(6, size // 8)
        edge = size + 2 * margin
        return edge, edge

    def _set_icon_size(self, size: int):
        self._current_size = size
        width, height = self._cell_size(size)
        self._grid.setIconSize(QSize(size, size))
        self._grid.setGridSize(QSize(width, height))
        for row in range(self._grid.count()):
            self._grid.item(row).setSizeHint(QSize(width, height))
        self._grid.doItemsLayout()

    def _update_status(self, *_):
        icons = self._selected_icons()
        if icons:
            names = ", ".join(icon.id for icon in icons[:3])
            self.statusBar().showMessage(f"{len(icons)} selected: {names}")
        else:
            self.statusBar().showMessage(f"{len(self._icons)} icons loaded")

    def _open_sprite(self):
        start_dir = (
            str(self._sprite_path.parent) if self._sprite_path else str(Path.home())
        )
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Sprite", start_dir, "SVG files (*.svg);;All files (*)"
        )
        if not path:
            return
        try:
            store = IconStore(Path(path), renderer=self._store.renderer)
        except (OSError, ET.ParseError) as error:
            QMessageBox.warning(
                self, "Open Sprite", f"Could not load '{path}':\n{error}"
            )
            return
        self.load_sprite(store, sprite_path=Path(path))

    def load_sprite(self, store, sprite_path: Path | None = None):
        """Replace the current sprite with a newly loaded one."""
        if sprite_path is not None:
            self._sprite_path = sprite_path
            self.setWindowTitle(self._title())
        self._store = store
        self._icons = store.icons
        self._master_icons = {}
        self._sync_renderer_controls()
        self._populate_grid()
        self._update_status()
        self._start_loading()

    def _show_context_menu(self, pos):
        item = self._grid.itemAt(pos)
        if item is None:
            return
        if not item.isSelected():
            self._grid.setCurrentItem(item)
        icons = self._selected_icons()
        menu = self._build_context_menu(icons)
        menu.exec(self._grid.viewport().mapToGlobal(pos))

    def _selected_icons(self) -> list[Icon]:
        """Icons currently selected, in grid order."""
        return [self._icons[index.row()] for index in self._grid.selectedIndexes()]

    def _build_context_menu(self, icons: list[Icon]) -> QMenu:
        """Actions act on the icons passed in; add future actions here."""
        menu = QMenu(self)
        menu.addAction("Copy id", lambda: self._copy_ids(icons))
        menu.addAction("Copy SVG", lambda: self._copy_svg(icons))
        return menu

    def _copy_ids(self, icons: list[Icon]):
        self._copy_to_clipboard("\n".join(icon.id for icon in icons), "id", len(icons))

    def _copy_svg(self, icons: list[Icon]):
        self._copy_to_clipboard(
            "\n".join(icon.svg for icon in icons), "SVG", len(icons)
        )

    def _copy_to_clipboard(self, text: str, what: str, count: int):
        QApplication.clipboard().setText(text)
        plural = "s" if count != 1 else ""
        self.statusBar().showMessage(
            f"Copied {what} of {count} icon{plural} to clipboard"
        )

    def _start_loading(self):
        self._generation += 1
        if self._loader and self._loader.isRunning():
            self._loader.requestInterruption()
        self._loader = IconLoader(
            self._store, enumerate(self._icons), self._generation, parent=self
        )
        self._loader.rendered.connect(self._on_rendered)
        self._loader.start()

    def _on_rendered(self, generation: int, index: int, image: QImage):
        if generation != self._generation:
            return  # stale result from a previous sprite
        self._master_icons[index] = image
        self._grid.item(index).setIcon(QIcon(QPixmap.fromImage(image)))

    def closeEvent(self, event):
        if self._loader:
            self._loader.requestInterruption()
            self._loader.wait(2000)
        super().closeEvent(event)
