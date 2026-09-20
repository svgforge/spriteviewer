"""Shared pytest fixtures for the sprite viewer tests."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    """A single QApplication shared by all tests that render icons."""
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])
