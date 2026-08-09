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

from preflightqc import __product_name__, __version__
from preflightqc.platform.paths import ensure_user_dirs


def _self_check() -> int:
    """Report what the application resolves at startup, then exit. No GUI, no window.

    The report is both printed and written to a file. The shipped executable is built for
    the Windows GUI subsystem, so a user who runs it from a console sees nothing on
    stdout — the text goes to a pipe that nothing is reading. Writing the same report to
    ``logs/self-check.txt`` is what makes this usable in the clean-machine run-book
    rather than only in a build script that captures output.
    """
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

    problems = report.problems()
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
    app.setOrganizationName(__product_name__)

    # Imported here rather than at module scope so that `ensure_user_dirs` runs before
    # anything tries to read configuration or profiles.
    from preflightqc.ui.main_window import MainWindow

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
