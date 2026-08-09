"""Architecture invariants (test strategy section 10).

Structural rules are cheaper to enforce mechanically than in review, and two of these
carry real weight:

* **No Qt below the UI layer** is what keeps the engine headlessly testable and what
  makes the ADR-001 GUI-framework fallback affordable.
* **No platform data in the engine or the UI** is what makes preset data the single
  place a platform rule can live.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent.parent / "src" / "preflightqc"

#: Layer index; a module may import from its own layer or any lower one.
LAYER_OF_PACKAGE = {
    "platform": 0,
    "adapters": 1,
    "core": 2,
    "normalise": 2,
    "rules": 3,
    "results": 3,
    "reporting": 4,
    "profiles": 4,
    "scan": 5,
    "orchestration": 5,
    "ui": 6,
    "cli": 6,
}

QT_MODULES = ("PySide6", "PyQt5", "PyQt6", "shiboken6")

PLATFORM_TOKENS = (
    "instagram",
    "tiktok",
    "youtube",
    "linkedin",
    "reels",
    "shorts",
    "facebook",
    "meta ",
)


def python_files(package: str) -> list[Path]:
    return sorted((SRC / package).rglob("*.py")) if (SRC / package).is_dir() else []


def all_python_files() -> list[Path]:
    return sorted(SRC.rglob("*.py"))


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
    return modules


def package_of(path: Path) -> str:
    return path.relative_to(SRC).parts[0] if len(path.relative_to(SRC).parts) > 1 else ""


def executable_source(path: Path) -> str:
    """The module's source with comments and docstrings removed.

    The platform-name scans below target *logic*, not prose. A docstring saying "this
    module knows nothing about Instagram" is exactly the documentation we want; only a
    platform name reachable by the running code is a violation.
    """
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))

    # A bare string expression statement is never meaningful code, so every one is
    # prose: module, class and function docstrings, and attribute docstrings alike.
    docstring_lines: set[int] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            docstring_lines.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))

    kept = [
        re.sub(r"#.*", "", line)
        for number, line in enumerate(text.splitlines(), start=1)
        if number not in docstring_lines
    ]
    return "\n".join(kept)


@pytest.mark.parametrize(
    "path", [p for p in all_python_files() if package_of(p) not in ("ui", "")], ids=str
)
def test_no_qt_below_the_ui_layer(path: Path) -> None:
    """The invariant that makes the GUI framework replaceable."""
    offenders = [m for m in imported_modules(path) if m.split(".")[0] in QT_MODULES]
    assert not offenders, f"{path} imports Qt: {offenders}"


@pytest.mark.parametrize("path", [p for p in all_python_files() if package_of(p)], ids=str)
def test_dependencies_point_downward_only(path: Path) -> None:
    package = package_of(path)
    own_layer = LAYER_OF_PACKAGE.get(package)
    if own_layer is None:
        pytest.skip(f"package '{package}' is not layered")

    for module in imported_modules(path):
        if not module.startswith("preflightqc."):
            continue
        parts = module.split(".")
        if len(parts) < 2:
            continue
        target_layer = LAYER_OF_PACKAGE.get(parts[1])
        if target_layer is None:
            continue
        assert target_layer <= own_layer, (
            f"{path} (layer {own_layer}) imports {module} (layer {target_layer}); "
            "dependencies must point downward only"
        )


@pytest.mark.parametrize("path", python_files("rules") + python_files("results"), ids=str)
def test_the_engine_names_no_platform(path: Path) -> None:
    """P3-A12 — the engine knows operators, not Instagram."""
    text = executable_source(path).lower()
    offenders = [token for token in PLATFORM_TOKENS if token in text]
    assert not offenders, f"{path} has platform names in executable code: {offenders}"


@pytest.mark.parametrize("path", python_files("ui"), ids=str)
def test_the_ui_names_no_platform(path: Path) -> None:
    """P6-A4 — platform names come from preset data, never from a widget."""
    text = executable_source(path).lower()
    offenders = [token for token in PLATFORM_TOKENS if token in text]
    assert not offenders, f"{path} has platform names in executable code: {offenders}"


@pytest.mark.parametrize("path", python_files("rules") + python_files("results"), ids=str)
def test_the_engine_hard_codes_no_platform_threshold(path: Path) -> None:
    """Sentinel values that only ever come from a platform specification.

    If one of these appears in engine code, a preset value has leaked out of data and
    into logic, which is exactly what spec 11.1 forbids.
    """
    forbidden = (
        "1920",
        "4096",
        "256000000000",
        "500000000",
        "300000000",
        "100000000",
        "5000000000",
        "0.563",
        "1.778",
        "2.4",
        "63999",
    )
    text = executable_source(path)
    offenders = [value for value in forbidden if value in text]
    assert not offenders, f"{path} hard-codes a platform threshold: {offenders}"


def test_every_package_has_a_layer_assignment() -> None:
    """A new package must be placed in the layering deliberately, not by accident."""
    packages = {p.name for p in SRC.iterdir() if p.is_dir() and not p.name.startswith("_")}
    packages.discard("schema")
    unassigned = packages - set(LAYER_OF_PACKAGE)
    assert not unassigned, f"packages missing a layer assignment: {unassigned}"
