#!/usr/bin/env python3
"""Install the Sprite Viewer and register it with the desktop environment.

Best-practice, cross-platform installer:

  * installs the Python package (plus PySide6) with pip
  * registers the app + icon in the user's session
      - Linux   : .desktop entry and hicolor icon in ~/.local/share
      - macOS   : an app bundle in ~/Applications
      - Windows : a Start Menu shortcut

Installs into the first of these that works:
    1. the active virtual environment  (when one is active)
    2. the current user's user site    (``pip --user``)
    3. a dedicated venv                (recommended for PEP 668 systems)

Usage:
    python3 install.py              # install for the current user (default)
    python3 install.py --system     # system-wide (requires root/admin)
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE = "spriteviewer"
APP_NAME = "Sprite Viewer"
PACKAGE_DIR = ROOT / "src" / PACKAGE
APP_ICON = PACKAGE_DIR / "spriteviewer.svg"

DESKTOP_ENTRY = """[Desktop Entry]
Type=Application
Version=1.0
Name={name}
GenericName=SVG sprite viewer
Comment=Browse the icons stored in an SVG sprite file
Exec={executable} %F
Icon={icon}
Terminal=false
Categories=Graphics;Viewer;
Keywords=svg;sprite;icons;
MimeType=image/svg+xml;
StartupNotify=true
"""

WINDOWS = os.name == "nt"


def log(message: str) -> None:
    print(f"* {message}")


def run(*command: str, **kwargs) -> None:
    log(" ".join(command))
    subprocess.check_call(list(command), **kwargs)


def bin_dir(venv: Path) -> Path:
    """Directory of executables inside a venv (Scripts on Windows, bin else)."""
    return venv / ("Scripts" if WINDOWS else "bin")


def venv_python(venv: Path) -> Path:
    return bin_dir(venv) / ("python.exe" if WINDOWS else "python")


# ------------------------------------------------------------------------- #
# Package installation
# ------------------------------------------------------------------------- #
def in_virtualenv() -> bool:
    return sys.prefix != sys.base_prefix or bool(os.environ.get("VIRTUAL_ENV"))


def install_package(python: str | Path, *flags: str) -> None:
    args = [str(python), "-m", "pip", "install", *flags, str(ROOT)]
    try:
        run(*args)
    except subprocess.CalledProcessError:
        log("retrying without build isolation")
        run(*args[:1], *(a for a in args[1:-1]), "--no-build-isolation", args[-1])


def app_venv() -> Path:
    """Location of the dedicated venv (per user)."""
    base = (
        Path(os.environ.get("LOCALAPPDATA", Path.home()))
        if WINDOWS
        else Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    )
    return base / "spriteviewer" / "venv"


def ensure_app_venv() -> Path:
    venv = app_venv()
    if not venv_python(venv).is_file():
        log(f"creating dedicated environment {venv}")
        run(sys.executable, "-m", "venv", str(venv))
    return venv


def console_script(venv: Path | None = None) -> Path:
    """Absolute path of the installed ``spriteviewer`` console script."""
    extension = ".exe" if WINDOWS else ""
    candidates = []
    if venv:
        candidates.append(bin_dir(venv) / (PACKAGE + extension))
    candidates += [
        shutil.which(PACKAGE),
        Path(sysconfig.get_path("scripts")) / (PACKAGE + extension),
        Path.home() / ".local" / "bin" / PACKAGE,
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    raise SystemExit(f"Could not find the installed '{PACKAGE}' command.")


# ------------------------------------------------------------------------- #
# Platform integration
# ------------------------------------------------------------------------- #
def install_linux(executable: Path, user: bool) -> None:
    data_home = (
        Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        if user
        else Path("/usr/share")
    )
    apps_dir = data_home / "applications"
    icons_dir = data_home / "icons" / "hicolor" / "scalable" / "apps"

    apps_dir.mkdir(parents=True, exist_ok=True)
    icons_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(APP_ICON, icons_dir / "spriteviewer.svg")

    desktop = DESKTOP_ENTRY.format(
        name=APP_NAME, executable=shlex.quote(str(executable)), icon=PACKAGE
    )
    dest = apps_dir / "spriteviewer.desktop"
    dest.write_text(desktop, encoding="utf-8")
    log(f"wrote {dest}")
    log(f"wrote icon {icons_dir / 'spriteviewer.svg'}")

    for cache_command, args in (
        ("update-desktop-database", [str(apps_dir)]),
        ("gtk-update-icon-cache", ["-f", "-t", str(data_home / "icons")]),
    ):
        if shutil.which(cache_command):
            try:
                run(cache_command, *args)
            except subprocess.CalledProcessError:
                log(f"'{cache_command}' failed (ignored)")


def install_macos(executable: Path) -> None:
    app_dir = Path.home() / "Applications" / f"{APP_NAME}.app"
    macos_dir = app_dir / "Contents" / "MacOS"
    resources_dir = app_dir / "Contents" / "Resources"
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)

    launcher = macos_dir / "launcher"
    launcher.write_text(
        f'#!/bin/sh\nexec {shlex.quote(str(executable))} "$@"\n', encoding="utf-8"
    )
    launcher.chmod(0o755)

    (app_dir / "Contents" / "Info.plist").write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>{APP_NAME}</string>
    <key>CFBundleExecutable</key><string>launcher</string>
    <key>CFBundleIdentifier</key><string>dev.spriteviewer.app</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleVersion</key><string>1.0</string>
    <key>CFBundleShortVersionString</key><string>1.0</string>
</dict>
</plist>
""",
        encoding="utf-8",
    )
    shutil.copy2(APP_ICON, resources_dir / "spriteviewer.svg")
    log(f"wrote {app_dir}")


def install_windows(executable: Path) -> None:
    programs = (
        Path(os.environ["APPDATA"])
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
    )
    programs.mkdir(parents=True, exist_ok=True)
    shortcut = programs / f"{APP_NAME}.lnk"

    script = (
        "$ws = New-Object -ComObject WScript.Shell;"
        f"$sc = $ws.CreateShortcut('{shortcut}');"
        f"$sc.TargetPath = '{executable}';"
        f"$sc.WorkingDirectory = '{os.path.dirname(executable)}';"
        f"$sc.Description = '{APP_NAME}';"
        "$sc.Save()"
    )
    run("powershell", "-NoProfile", "-NonInteractive", "-Command", script)
    log(f"wrote shortcut {shortcut}")


# ------------------------------------------------------------------------- #
# Entry point
# ------------------------------------------------------------------------- #
def main() -> None:
    system = "--system" in sys.argv[1:]

    install_venv = None
    if system:
        log("system-wide install (requires root/admin)")
        install_package(sys.executable)
    elif in_virtualenv():
        log("installing into the active virtual environment")
        install_package(sys.executable)
    else:
        try:
            log("installing into the user's site-packages")
            install_package(sys.executable, "--user")
        except subprocess.CalledProcessError:
            log("user install unavailable (PEP 668); using a dedicated venv")
            install_venv = ensure_app_venv()
            install_package(venv_python(install_venv))

    executable = console_script(install_venv)
    log(f"entry point: {executable}")

    if WINDOWS:
        install_windows(executable)
    elif sys.platform == "darwin":
        install_macos(executable)
    else:
        install_linux(executable, user=not system)

    log(f"done. Run {executable} to start {APP_NAME}.")


if __name__ == "__main__":
    main()
