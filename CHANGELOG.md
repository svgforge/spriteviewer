# Changelog

## 0.3 — 2026-11-21

### Added
- Support for svgforge sprite modes: `symbol`, `defs`, `stack`, and `view`.

### Changed
- Minimum Python version is now 3.10+; PySide6 dependency updated to 6.12+.
- Empty-state message now reads "No icons found in SVG sprite".

### Fixed
- SVG `viewBox` parsing now accepts comma-separated values.
- XML parsing is hardened against entity expansion in untrusted SVG files.
- Windows installer now escapes single quotes in PowerShell shortcut paths.

## 0.2 — 2026-09-23

### Added
- Support for compressed sprite files: `.svgz`/`.svg.gz` (gzip) and `.svg.zip`
  (zip containing exactly one `.svg`; multiple `.svg` members raise a clear
  error).
- Empty-state notice ("no valid svg file with symbols") when the sprite file
  contains no `<symbol>` fragments — the app still opens normally.

### Changed
- Icon selection now highlights the whole cell with a small border radius and
  a minimum 2 px gap between selected icons; the rendering behaves the same
  across themes and operating systems and uses the theme palette colors.
- Development rules (AGENTS.md) are now in English and require everything
  (code, documentation, commits, communication) to be written in English.
