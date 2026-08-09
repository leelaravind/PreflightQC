"""Shared pytest configuration and fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# `tools/` and `packaging/` are release scripts, not installed packages. They enforce the
# licensing gates, so they need tests as much as the application does — make them
# importable by name.
for scripts in ("tools", "packaging"):
    if str(REPO_ROOT / scripts) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / scripts))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def presets_dir() -> Path:
    return REPO_ROOT / "presets"


# `tests/factories.py` is imported by name from test modules in subdirectories.
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))
