"""Regression for the second Phase 13 clean-machine launch failure (2026-08-14).

Release candidate ``0563117b…d43386`` fixed the first clean-machine failure (the
``urllib.request`` exclusion), passed every build gate, installed on a fresh Windows 11
x64 VM, and died on first launch:

    [Errno 2] No such file or directory:
    C:\\...\\PreflightQC\\_internal\\preflightqc\\rules\\schema\\preset.schema.json

The launch path — app → main_window → ``_load_presets`` → rules.loader — reads the
preset schema relative to ``__file__``, which in a one-dir freeze resolves under
``_internal/preflightqc/…``. The spec's ``datas`` declared only the icon, so the schema
never shipped. Every gate passed anyway: the self-check imported the launch closure
(the fix for the *first* failure) but never read any package data.

These tests close that hole from both ends, mirroring
``test_frozen_import_closure.py``:

* ``TestManifestAgainstSourceTree`` runs on **every machine, every time**: any
  non-Python file inside ``src/preflightqc`` that is not declared in
  ``packaging/frozen_datas.py`` fails the suite the day it is added, and every
  ``__file__``-relative resource path the runtime actually uses must resolve to a
  declared entry.
* ``TestStartupResourcePathInAFrozenShapedLayout`` rebuilds the package layout a freeze
  produces — the declared data files and nothing else — and runs the real loader
  against the real shipped presets inside it, in a fresh interpreter.
* ``TestFrozenDataInTheBuiltPackage`` runs against the built artefact and asserts the
  data actually shipped and the packaged self-check actually performed the reads.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import frozen_datas
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src"
PACKAGE = REPO_ROOT / "dist" / "PreflightQC"

#: The one file whose absence crashed the second candidate on a clean machine.
REGRESSION_FILE = "preflightqc/rules/schema/preset.schema.json"


def package_data_files_in_the_source_tree() -> set[str]:
    """Every non-Python file inside the installed package, as POSIX-relative paths."""
    return {
        path.relative_to(SRC).as_posix()
        for path in (SRC / "preflightqc").rglob("*")
        if path.is_file() and path.suffix != ".py" and "__pycache__" not in path.parts
    }


class TestManifestAgainstSourceTree:
    """The data manifest and the source tree must never disagree, in either direction."""

    def test_every_package_data_file_in_the_source_tree_is_declared(self) -> None:
        undeclared = package_data_files_in_the_source_tree() - set(frozen_datas.PACKAGE_DATA)
        assert not undeclared, (
            "these files live inside src/preflightqc but are not declared in "
            "packaging/frozen_datas.py, so a frozen build will not ship them and any "
            "code that reads them relative to __file__ will crash on a clean machine "
            f"— the exact Phase 13 failure mode of 2026-08-14: {sorted(undeclared)}"
        )

    def test_every_declared_file_exists_and_freezes_beside_its_module(self) -> None:
        for source, destination in frozen_datas.pyinstaller_datas(REPO_ROOT):
            assert Path(source).is_file()
            # Code finds these via Path(__file__).parent, so the frozen destination
            # must be the file's own package directory — nothing else can work.
            relative = Path(source).relative_to(SRC)
            assert destination == relative.parent.as_posix()

    def test_the_scan_is_not_vacuous(self) -> None:
        """A completeness check over an empty scan proves nothing: the scanner must
        actually see the three resources known to exist today."""
        found = package_data_files_in_the_source_tree()
        assert REGRESSION_FILE in found
        assert "preflightqc/reporting/templates/report.html.j2" in found
        assert "preflightqc/ui/assets/preflightqc.png" in found

    def test_the_regression_file_itself_is_covered(self) -> None:
        assert REGRESSION_FILE in frozen_datas.PACKAGE_DATA

    def test_every_runtime_resource_path_resolves_to_a_declared_entry(self) -> None:
        """The paths the running code actually uses, not paths this test re-derives.

        If SCHEMA_PATH, the template directory or the icon path is ever moved or
        renamed without the manifest following, this fails on the dev machine.
        """
        from preflightqc.reporting import html_renderer
        from preflightqc.rules import loader
        from preflightqc.ui import branding

        runtime_paths = (
            loader.SCHEMA_PATH,
            html_renderer.TEMPLATE_DIR / html_renderer.TEMPLATE_NAME,
            branding.ICON_PATH,
        )
        for path in runtime_paths:
            relative = path.resolve().relative_to(SRC).as_posix()
            assert relative in frozen_datas.PACKAGE_DATA, (
                f"{relative} is read at runtime relative to __file__ but is not in "
                "frozen_datas.PACKAGE_DATA"
            )


_LOADER_SCRIPT = textwrap.dedent(
    """
    from pathlib import Path

    from preflightqc.rules.loader import load_catalog

    catalog = load_catalog([Path({presets!r})])
    assert catalog.presets, "no presets loaded"
    assert not catalog.rejected, f"rejected: {{catalog.rejected}}"
    print(f"catalog OK ({{len(catalog.presets)}} presets)")
    """
)


class TestStartupResourcePathInAFrozenShapedLayout:
    """The launch's data reads, exercised against the layout a freeze produces.

    The layout is rebuilt from the manifest: every ``.py`` file (a stand-in for the
    PYZ archive) plus **only** the declared data files. The subprocess then runs the
    real startup chain — load_catalog → build_preset → _validator → _schema — over the
    real shipped presets. A manifest that omits a launch-critical resource fails here,
    on every dev machine, the same day.
    """

    @pytest.fixture
    def frozen_shaped_site(self, tmp_path: Path) -> Path:
        site = tmp_path / "_internal"
        for module in (SRC / "preflightqc").rglob("*.py"):
            if "__pycache__" in module.parts:
                continue
            target = site / module.relative_to(SRC)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(module, target)
        for relative in frozen_datas.PACKAGE_DATA:
            target = site / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SRC / relative, target)
        return site

    def _run(self, site: Path) -> subprocess.CompletedProcess[str]:
        script = _LOADER_SCRIPT.format(presets=str(REPO_ROOT / "presets"))
        return subprocess.run(  # noqa: S603 - our own interpreter, generated argv
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=180,
            env={**os.environ, "PYTHONPATH": str(site)},
            check=False,
        )

    def test_the_real_presets_load_through_the_real_loader(self, frozen_shaped_site: Path) -> None:
        result = self._run(frozen_shaped_site)
        assert result.returncode == 0, (
            "the startup preset load fails in a frozen-shaped layout built from the "
            "data manifest — this is the exact failure mode that reached a clean "
            "machine in Phase 13 (2026-08-14):\n" + result.stderr
        )
        assert "catalog OK" in result.stdout

    def test_the_layout_actually_gates_on_the_manifest(self, frozen_shaped_site: Path) -> None:
        """A guard that cannot fail proves nothing: removing the schema from the layout
        must reproduce the clean-machine crash, or this whole file is theatre."""
        (frozen_shaped_site / REGRESSION_FILE).unlink()
        result = self._run(frozen_shaped_site)
        assert result.returncode != 0
        assert "preset.schema.json" in result.stderr

    def test_the_shipped_presets_validate_in_this_source_tree_too(self) -> None:
        """The same chain in-process: main_window._load_presets calls exactly this."""
        from preflightqc.platform.paths import shipped_presets_dir
        from preflightqc.rules.loader import load_catalog

        catalog = load_catalog([shipped_presets_dir()])
        assert catalog.presets
        assert catalog.rejected == ()


@pytest.mark.skipif(not PACKAGE.is_dir(), reason="no built package; run packaging/build.py")
class TestFrozenDataInTheBuiltPackage:
    """Assertions about the artefact that ships, not the environment that built it."""

    def test_every_declared_data_file_shipped_under_internal(self) -> None:
        missing = [
            relative
            for relative in frozen_datas.PACKAGE_DATA
            if not (PACKAGE / "_internal" / Path(relative)).is_file()
        ]
        assert not missing, (
            f"declared package data absent from the built package: {missing} — the "
            "frozen app will crash reading them on a machine with no source tree"
        )

    def test_the_shipped_schema_is_the_schema_that_was_reviewed(self) -> None:
        shipped = PACKAGE / "_internal" / Path(REGRESSION_FILE)
        assert json.loads(shipped.read_text(encoding="utf-8")) == json.loads(
            (SRC / REGRESSION_FILE).read_text(encoding="utf-8")
        )

    def test_the_frozen_self_check_performs_the_launch_data_reads(self) -> None:
        """The packaged --self-check must load the preset catalogue through the real
        loader and load the report template, and say so — that is the gate that makes
        a data-shipping regression fail on the build machine, not a customer's."""
        result = subprocess.run(  # noqa: S603 - absolute path, argv list, no shell
            [str(PACKAGE / "PreflightQC.exe"), "--self-check"],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "preset catalogue : OK" in result.stdout
        assert "report template  : OK" in result.stdout
