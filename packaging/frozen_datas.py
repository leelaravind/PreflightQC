"""The freeze's package-data manifest — one list, imported by the spec AND by the tests.

This file exists because of the *second* Phase 13 clean-machine failure (2026-08-14):
release candidate ``0563117b…d43386`` fixed the ``urllib.request`` exclusion, installed
cleanly on a fresh Windows 11 VM, and then died on first launch with::

    [Errno 2] No such file or directory:
    C:\\...\\PreflightQC\\_internal\\preflightqc\\rules\\schema\\preset.schema.json

The launch path — app → main_window → ``_load_presets`` → rules.loader — reads the
preset schema relative to ``__file__`` (``loader.SCHEMA_PATH``). In the frozen build
that resolves under ``_internal/preflightqc/…``, and the spec's ``datas`` declared only
the icon, so the schema simply never shipped. Every gate passed anyway, because the
self-check *imported* the launch closure (the fix for the first failure) but never
*read* any package data. Same lesson as last time, applied to data instead of modules:

1. The data list must be testable against the source tree on every dev machine.
   ``tests/packaging/test_frozen_data_resources.py`` imports this list and fails if any
   non-Python file inside ``src/preflightqc`` is not declared here — so adding a
   resource without shipping it fails the suite the same day, not on a customer's
   machine.
2. The self-check must exercise the same data reads the launch performs: it now loads
   the shipped preset catalogue through the real loader (schema + validator) and loads
   the report template (``preflightqc.ui.app._self_check``), and the build gate runs it
   against the frozen package.

Scope: this manifest is only for **package-internal** data — files Python code reads
relative to ``__file__``, which PyInstaller must place under ``_internal/``. The
root-staged payload (``presets/``, ``licenses/``, ``bin/``) is deliberately NOT here:
it is staged beside the executable by ``packaging/build.py`` because ADR-001 §5 puts it
at the package root, and ``layout_check.py`` verifies that separately.
"""

from __future__ import annotations

from pathlib import Path

#: Every non-Python file inside the ``preflightqc`` package that runtime code reads.
#: Paths are relative to ``src/``, POSIX-style. The PyInstaller destination is always
#: the file's own package directory — code finds these via ``Path(__file__).parent``,
#: so source layout and frozen layout must be identical.
PACKAGE_DATA: tuple[str, ...] = (
    # rules.loader.SCHEMA_PATH — read on the first preset load, i.e. at launch.
    "preflightqc/rules/schema/preset.schema.json",
    # reporting.html_renderer.TEMPLATE_DIR — read on the first HTML report export.
    "preflightqc/reporting/templates/report.html.j2",
    # ui.branding.ICON_PATH — the window icon (Product Owner-approved logo; see
    # assets/logo/PROVENANCE.md).
    "preflightqc/ui/assets/preflightqc.png",
)


def pyinstaller_datas(repo_root: Path) -> list[tuple[str, str]]:
    """The manifest in the shape PyInstaller's ``Analysis(datas=…)`` consumes.

    Raises if a declared file does not exist: a build must not silently proceed past a
    manifest entry that no longer matches the source tree.
    """
    entries: list[tuple[str, str]] = []
    for relative in PACKAGE_DATA:
        source = repo_root / "src" / Path(relative)
        if not source.is_file():
            raise FileNotFoundError(
                f"frozen_datas.PACKAGE_DATA names {relative}, which does not exist "
                f"under {repo_root / 'src'}"
            )
        entries.append((str(source), Path(relative).parent.as_posix()))
    return entries
