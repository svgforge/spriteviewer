# Changelog

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
