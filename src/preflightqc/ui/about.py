"""The About dialog.

Renders entirely offline. This is not incidental: the FFmpeg LGPL checklist requires an
about-box notice, and a licence notice that only appears when the machine has a network
connection is not a notice.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from preflightqc import __product_name__, __version__
from preflightqc.platform.binaries import StartupReport
from preflightqc.platform.paths import application_root
from preflightqc.reporting import claims

#: The notices the FFmpeg and MediaInfo licences require in an about box. The full texts
#: ship in the licences folder; these are the sentences that must be visible in-product.
REQUIRED_NOTICES = (
    "This software uses libraries from the FFmpeg project under the LGPLv3.",
    "PreflightQC does not own FFmpeg. FFmpeg is the property of its copyright holders.",
    "The bundled FFmpeg build is configured with --enable-version3 and is therefore "
    "under the GNU Lesser General Public License version 3.",
    "This product uses MediaInfo library, Copyright (c) 2002-2026 MediaArea.net SARL.",
    "ZenLib — (c) MediaArea.net SARL, zlib license.",
)


def _licence_files() -> list[Path]:
    folder = application_root() / "licenses"
    return sorted(folder.glob("*.txt")) if folder.is_dir() else []


class AboutDialog(QDialog):
    def __init__(self, startup: StartupReport, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {__product_name__}")
        self.resize(680, 520)

        tabs = QTabWidget()
        tabs.addTab(self._about_tab(startup), "About")
        tabs.addTab(self._notices_tab(), "Third-party notices")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    def _about_tab(self, startup: StartupReport) -> QTextBrowser:
        view = QTextBrowser()
        view.setOpenExternalLinks(False)
        versions = "".join(
            f"<li>{name}: {version}</li>" for name, version in sorted(startup.versions().items())
        )
        problems = "".join(f"<li>{problem}</li>" for problem in startup.problems())
        view.setHtml(
            f"<h2>{__product_name__} {__version__}</h2>"
            "<p>Offline technical QA for video exports.</p>"
            f"<p>{claims.APPROVED_CLAIM}</p>"
            f"<p>{claims.NON_DESTRUCTIVE_STATEMENT}</p>"
            f"<p>{claims.ACCURACY_STATEMENT}</p>"
            "<h3>Inspection tools</h3>"
            f"<ul>{versions or '<li>none available</li>'}</ul>"
            + (f"<h3>Problems</h3><ul>{problems}</ul>" if problems else "")
            + "<h3>Privacy</h3>"
            "<p>PreflightQC performs no network requests. No file, metadata or result "
            "leaves this machine.</p>"
        )
        return view

    def _notices_tab(self) -> QTextBrowser:
        view = QTextBrowser()
        view.setOpenExternalLinks(False)
        notices = "".join(f"<p>{notice}</p>" for notice in REQUIRED_NOTICES)
        files = _licence_files()
        listing = (
            "".join(f"<li>{path.name}</li>" for path in files)
            if files
            else "<li>Licence texts are installed with the release package.</li>"
        )
        view.setHtml(
            "<h3>Third-party notices</h3>"
            f"{notices}"
            "<p>Full licence texts, the exact build configuration of the bundled "
            "FFmpeg, and a link to its corresponding source are included with the "
            "installed product.</p>"
            f"<ul>{listing}</ul>"
        )
        return view
