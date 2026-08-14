"""Application entry point.

    python -m preflightqc.ui.app
    python -m preflightqc.ui.app --self-check

``--self-check`` is release-validation infrastructure, not a product feature. Several
acceptance criteria are about the *packaged* application — that it launches with no Python
on the machine (P13-A3), that it reports both inspector versions (P13-A4), and that it
resolves inspectors by absolute path and never from PATH (P11-A9, P13-A5, spec AC-17).
Without a non-interactive entry point, every one of those could only be checked by a human
opening a dialog and reading it, which is not a check that can be run on every build.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from preflightqc import __product_name__, __publisher__, __version__
from preflightqc.platform.paths import ensure_user_dirs


def _self_check() -> int:
    """Report what the application resolves at startup, then exit. No GUI, no window.

    The report is both printed and written to a file. The shipped executable is built for
    the Windows GUI subsystem, so a user who runs it from a console sees nothing on
    stdout — the text goes to a pipe that nothing is reading. Writing the same report to
    ``logs/self-check.txt`` is what makes this usable in the clean-machine run-book
    rather than only in a build script that captures output.
    """
    import importlib

    from preflightqc.platform import binaries
    from preflightqc.platform.paths import (
        application_root,
        bundled_binaries_dir,
        shipped_presets_dir,
        user_logs_dir,
    )

    lines = [
        f"{__product_name__} {__version__}",
        f"frozen           : {getattr(sys, 'frozen', False)}",
        f"application root : {application_root()}",
        f"inspector dir    : {bundled_binaries_dir()}",
        f"presets dir      : {shipped_presets_dir()}",
    ]

    # The exact modules the GUI launch imports, in launch order. The first 1.0.0
    # candidate passed this self-check and then crashed on a clean machine at the
    # `main_window` import, because the freeze had excluded a stdlib module jsonschema
    # needs (urllib.request). A self-check that skips the launch closure certifies
    # nothing about the launch — so it no longer skips it. Import failures here are
    # reported as problems, which makes this exit non-zero and fails the build gate.
    launch_closure = (
        "preflightqc.ui.branding",
        "preflightqc.ui.theme",
        "preflightqc.ui.main_window",
        "preflightqc.profiles.compiler",
        "preflightqc.rules.loader",
        "jsonschema",
    )
    import_failures: list[str] = []
    for module_name in launch_closure:
        try:
            importlib.import_module(module_name)
        except Exception as error:  # any failure here is release-blocking
            import_failures.append(f"{module_name}: {type(error).__name__}: {error}")
    closure_status = (
        f"FAILED ({len(import_failures)})"
        if import_failures
        else f"OK ({len(launch_closure)} modules)"
    )
    lines.append(f"import closure   : {closure_status}")
    lines.extend(f"    {failure}" for failure in import_failures)

    # The exact data reads the GUI launch performs, not merely the imports. The second
    # 1.0.0 candidate passed the import-closure check above and then crashed on a clean
    # machine because the preset *schema file* — data, not a module — never shipped
    # (Phase 13, 2026-08-14; see packaging/frozen_datas.py). Importing a module proves
    # nothing about the files it reads lazily, so this check performs the reads:
    # the shipped catalogue through the real loader (schema + validator), and the HTML
    # report template through the real renderer environment.
    data_failures: list[str] = []
    preset_count = 0
    try:
        from preflightqc.rules.loader import load_catalog

        catalog = load_catalog([shipped_presets_dir()])
        preset_count = len(catalog.presets)
        if preset_count == 0:
            data_failures.append(f"no shipped presets loaded from {shipped_presets_dir()}")
        for path, reason in catalog.rejected:
            data_failures.append(f"shipped preset rejected: {path}: {reason}")
    except Exception as error:  # any failure here is release-blocking
        data_failures.append(f"preset catalogue: {type(error).__name__}: {error}")
    lines.append(
        "preset catalogue : "
        + ("FAILED" if data_failures else f"OK ({preset_count} presets, schema validated)")
    )

    template_failure: str | None = None
    try:
        from preflightqc.reporting import html_renderer

        html_renderer._environment().get_template(html_renderer.TEMPLATE_NAME)
    except Exception as error:  # any failure here is release-blocking
        template_failure = f"report template: {type(error).__name__}: {error}"
        data_failures.append(template_failure)
    lines.append(f"report template  : {'FAILED' if template_failure else 'OK'}")

    report = binaries.check_all()
    for info in report.inspectors:
        lines.extend(
            [
                "",
                f"{info.kind.value}",
                f"  available    : {info.available}",
                f"  path         : {info.path}",
                f"  version      : {info.version}",
                f"  licence      : {info.licence}",
            ]
        )
        if info.licence_violations:
            lines.append(f"  VIOLATIONS   : {', '.join(info.licence_violations)}")
        if not info.available:
            lines.append(f"  message      : {info.message}")

    problems = [
        *(f"launch import closure broken: {failure}" for failure in import_failures),
        *(f"launch data resource broken: {failure}" for failure in data_failures),
        *report.problems(),
    ]
    if problems:
        lines.append("")
        lines.append("SELF-CHECK FAILED")
        lines.extend(f"  - {problem}" for problem in problems)
    else:
        lines.extend(["", "SELF-CHECK PASSED"])

    text = "\n".join(lines)
    print(text)
    try:
        destination = user_logs_dir() / "self-check.txt"
        destination.write_text(text + "\n", encoding="utf-8")
        print(f"\nWritten to {destination}")
    except OSError as error:  # pragma: no cover - only on an unwritable profile
        print(f"\nCould not write the self-check report: {error}")

    return 1 if problems else 0


def main() -> int:
    if "--version" in sys.argv:
        print(f"{__product_name__} {__version__}")
        return 0

    ensure_user_dirs()

    if "--self-check" in sys.argv:
        return _self_check()

    app = QApplication(sys.argv)
    app.setApplicationName(__product_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(__publisher__)

    from preflightqc.ui.branding import application_icon

    icon = application_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    from preflightqc.ui.theme import apply_theme

    apply_theme(app)

    # Imported here rather than at module scope so that `ensure_user_dirs` runs before
    # anything tries to read configuration or profiles.
    from preflightqc.ui.main_window import MainWindow

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
