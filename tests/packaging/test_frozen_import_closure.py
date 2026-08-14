"""Regression for the Phase 13 clean-machine launch failure (2026-08-12).

Release candidate ``d9e6f907…aadf05f`` passed all twelve build gates, installed on a
fresh Windows 11 x64 VM, and died on first launch:

    Failed to execute script 'app' due to unhandled exception:
    No module named 'urllib.request'

The spec had excluded ``urllib.request`` to strengthen the no-network posture, but
``jsonschema`` imports it at module scope, so the launch path (app → main_window →
profiles.compiler → rules.loader → jsonschema) could not be imported at all. Every gate
passed anyway, because no gate exercised that import path under the freeze's exclusions.

These tests close that hole from both ends:

* ``TestExclusionsAgainstLaunchClosure`` runs on **every machine, every time**: a fresh
  interpreter in which every excluded module is made unimportable, importing the real
  launch closure. Adding an exclude the runtime needs fails here, on the dev machine,
  the same day — not on a customer's.
* ``TestFrozenClosureInTheBuiltPackage`` runs against the built artefact and asserts the
  required closure actually shipped and the still-banned transport stack did not.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import frozen_excludes
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE = REPO_ROOT / "dist" / "PreflightQC"

#: The modules the GUI launch imports, in launch order — the exact chain from the
#: clean-machine traceback, plus the lazily imported UI modules from app.main().
LAUNCH_CLOSURE = (
    "preflightqc.ui.app",
    "preflightqc.ui.branding",
    "preflightqc.ui.theme",
    "preflightqc.ui.about",
    "preflightqc.ui.main_window",
    "preflightqc.profiles.compiler",
    "preflightqc.rules.loader",
    "preflightqc.platform.binaries",
    "jsonschema",
)

_BLOCKER_TEMPLATE = textwrap.dedent(
    """
    import importlib, sys

    EXCLUDES = {excludes!r}

    class FrozenExclusionBlocker:
        '''Raise exactly what a PyInstaller freeze raises for an excluded module.'''
        def find_spec(self, name, path=None, target=None):
            for excluded in EXCLUDES:
                if name == excluded or name.startswith(excluded + "."):
                    raise ModuleNotFoundError(f"No module named {{name!r}}")
            return None

    sys.meta_path.insert(0, FrozenExclusionBlocker())

    for module_name in {closure!r}:
        importlib.import_module(module_name)

    # Not just importable — the validator the rules loader relies on must work.
    import jsonschema
    jsonschema.Draft202012Validator({{"type": "object"}}).validate({{}})
    print("closure OK")
    """
)


class TestExclusionsAgainstLaunchClosure:
    """The spec's exclusion list must be compatible with the launch import closure."""

    def test_the_launch_closure_imports_with_every_exclusion_enforced(self) -> None:
        script = _BLOCKER_TEMPLATE.format(
            excludes=tuple(frozen_excludes.EXCLUDES), closure=LAUNCH_CLOSURE
        )
        result = subprocess.run(  # noqa: S603 - our own interpreter, generated argv
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=180,
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
            check=False,
        )
        assert result.returncode == 0, (
            "the launch import closure breaks under the freeze's exclusions — this is "
            "the exact failure mode that reached a clean machine in Phase 13:\n"
            + result.stderr
        )
        assert "closure OK" in result.stdout

    def test_the_required_stdlib_closure_is_not_excluded(self) -> None:
        """The documented required closure and the exclusion list must never overlap."""
        for required in frozen_excludes.REQUIRED_STDLIB_CLOSURE:
            for excluded in frozen_excludes.EXCLUDES:
                assert not (
                    required == excluded or required.startswith(excluded + ".")
                ), f"{required} is required at runtime but excluded by {excluded}"

    def test_the_regression_module_itself_is_covered(self) -> None:
        """urllib.request being importable is the specific Phase 13 regression."""
        assert "urllib.request" in frozen_excludes.REQUIRED_STDLIB_CLOSURE
        assert "urllib.request" not in frozen_excludes.EXCLUDES

    def test_the_blocker_actually_blocks(self) -> None:
        """A guard that cannot fail proves nothing: excluding a closure module must
        make the closure test fail, or the whole file is theatre."""
        script = _BLOCKER_TEMPLATE.format(
            excludes=(*frozen_excludes.EXCLUDES, "urllib.request"), closure=LAUNCH_CLOSURE
        )
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=180,
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
            check=False,
        )
        assert result.returncode != 0
        assert "urllib.request" in result.stderr


@pytest.mark.skipif(not PACKAGE.is_dir(), reason="no built package; run packaging/build.py")
class TestFrozenClosureInTheBuiltPackage:
    """Assertions about the artefact that ships, not the environment that built it."""

    def test_the_socket_extension_ships(self) -> None:
        """_socket must be in the package: urllib.request imports socket unconditionally
        at module scope, and jsonschema imports urllib.request. Its absence is precisely
        the state that crashed the first candidate on a clean machine."""
        assert list(PACKAGE.rglob("_socket.pyd")), (
            "_socket.pyd is missing from the package; the frozen app cannot import "
            "jsonschema and will crash at launch on a machine with no system Python"
        )

    def test_no_tls_stack_ships(self) -> None:
        """The posture that replaced 'no socket implementation at all': the socket
        module ships because the import graph demands it, but no TLS stack does."""
        assert not list(PACKAGE.rglob("_ssl.pyd"))
        assert not [p for p in PACKAGE.rglob("*") if p.name.lower().startswith("libssl")]

    def test_the_frozen_self_check_verifies_the_import_closure(self) -> None:
        """The packaged --self-check must import the launch closure and say so, so the
        build gate fails on the build machine if the freeze drops a runtime module."""
        result = subprocess.run(  # noqa: S603 - absolute path, argv list, no shell
            [str(PACKAGE / "PreflightQC.exe"), "--self-check"],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "import closure   : OK" in result.stdout
