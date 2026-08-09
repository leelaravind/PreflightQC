"""The About dialog.

Renders entirely offline. This is not incidental: the FFmpeg LGPL checklist requires an
about-box notice, and a licence notice that only appears when the machine has a network
connection is not a notice.

The URLs shown here are text. Nothing in this dialog opens a socket, resolves a name or
checks whether an address exists — `setOpenExternalLinks(False)` is set for that reason
and the addresses are selectable so a user can copy one into their own browser. Displaying
a URL must never become the reason a product that promises no network makes a request.
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

from preflightqc import (
    LEGAL_URL,
    PRODUCT_URL,
    SOURCE_URL,
    SUPPORT_URL,
    __product_name__,
    __publisher__,
    __version__,
)
from preflightqc.platform.binaries import StartupReport
from preflightqc.platform.paths import application_root
from preflightqc.reporting import claims
from preflightqc.ui import design as d

#: The notices the FFmpeg and MediaInfo licences require in an about box. The full texts
#: ship in the licences folder; these are the sentences that must be visible in-product.
REQUIRED_NOTICES = (
    "This software uses libraries from the FFmpeg project under the LGPLv3.",
    "PreflightQC does not own FFmpeg. FFmpeg is the property of its copyright holders.",
    "The bundled FFmpeg build is configured with --enable-version3 and is therefore "
    "under the GNU Lesser General Public License version 3.",
    "This product uses MediaInfo library, Copyright (c) 2002-2026 MediaArea.net SARL.",
    "ZenLib — (c) MediaArea.net SARL, zlib license.",
    "This software uses the Qt toolkit via PySide6 under the LGPLv3.",
)


def _licence_files() -> list[Path]:
    folder = application_root() / "licenses"
    return sorted(folder.glob("*.txt")) if folder.is_dir() else []


class AboutDialog(QDialog):
    def __init__(self, startup: StartupReport, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {__product_name__}")
        self.resize(760, 580)

        tabs = QTabWidget()
        tabs.addTab(self._about_tab(startup), "About")
        tabs.addTab(self._notices_tab(), "Third-party notices")
        self._tabs = tabs

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(d.SPACE_XL, d.SPACE_XL, d.SPACE_XL, d.SPACE_XL)
        layout.setSpacing(d.SPACE_LG)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    def _view(self) -> QTextBrowser:
        view = QTextBrowser()
        view.setOpenExternalLinks(False)
        view.setOpenLinks(False)
        return view

    def _about_tab(self, startup: StartupReport) -> QTextBrowser:
        view = self._view()
        view.setAccessibleName("About PreflightQC")

        # The approved logo, as a document resource so the offline promise holds:
        # nothing here resolves a URL. Degrades to no image if the asset is absent.
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QTextDocument

        from preflightqc.ui.branding import logo_pixmap

        pixmap = logo_pixmap(96)
        logo_html = ""
        if not pixmap.isNull():
            view.document().addResource(
                QTextDocument.ResourceType.ImageResource, QUrl("preflightqc-logo"), pixmap
            )
            logo_html = "<img src='preflightqc-logo' width='96' height='96'>"

        inspectors = "".join(
            f"<tr><td style='color:{d.TEXT_SECONDARY};padding-right:16px'>{name}</td>"
            f"<td style='font-family:{d.FONT_MONO};color:{d.TEXT_PRIMARY}'>"
            f"{info.version or 'unknown'}</td>"
            f"<td style='color:{d.TEXT_MUTED};padding-left:16px'>{info.licence or ''}</td></tr>"
            for name, info in sorted(
                (i.kind.value, i) for i in startup.inspectors if i.available
            )
        )
        problems = "".join(f"<li>{problem}</li>" for problem in startup.problems())

        view.setHtml(
            logo_html
            + f"<div style='font-size:{d.TYPE_DISPLAY}pt;font-weight:600;"
            f"color:{d.TEXT_PRIMARY}'>{__product_name__}</div>"
            f"<div style='font-family:{d.FONT_MONO};color:{d.TEXT_MUTED};margin-top:2px'>"
            f"{__version__}</div>"
            f"<div style='color:{d.TEXT_SECONDARY};margin-top:10px'>"
            f"Offline technical QA for video deliverables, from {__publisher__}.</div>"
            f"<p style='color:{d.TEXT_PRIMARY};margin-top:16px'>{claims.APPROVED_CLAIM}</p>"
            f"<p style='color:{d.TEXT_SECONDARY}'>{claims.NON_DESTRUCTIVE_STATEMENT}</p>"
            f"<p style='color:{d.TEXT_SECONDARY}'>{claims.ACCURACY_STATEMENT}</p>"
            f"<div style='color:{d.TEXT_SECONDARY};font-weight:600;margin-top:18px'>"
            "Inspection tools</div>"
            f"<table cellpadding='2' style='margin-top:4px'>{inspectors or ''}</table>"
            + (
                f"<div style='color:{d.FAIL_TONE.foreground};font-weight:600;margin-top:16px'>"
                f"Problems</div><ul>{problems}</ul>"
                if problems
                else ""
            )
            + f"<div style='color:{d.TEXT_SECONDARY};font-weight:600;margin-top:18px'>"
            "Privacy</div>"
            f"<p style='color:{d.TEXT_SECONDARY}'>PreflightQC makes no network requests and "
            "has no account, no telemetry and no update check. No file, no metadata and no "
            "result leaves this machine. Source files are opened read-only.</p>"
            f"<div style='color:{d.TEXT_SECONDARY};font-weight:600;margin-top:18px'>"
            f"{__publisher__}</div>"
            f"<table cellpadding='2' style='margin-top:4px'>"
            f"{_link_row('Product', PRODUCT_URL)}"
            f"{_link_row('Support', SUPPORT_URL)}"
            f"{_link_row('Licence and legal', LEGAL_URL)}"
            f"{_link_row('Open-source components', SOURCE_URL)}"
            f"</table>"
            f"<p style='color:{d.TEXT_MUTED};font-size:{d.TYPE_CAPTION}pt;margin-top:10px'>"
            "These addresses are shown for reference. PreflightQC does not open them, and "
            "nothing in the product requires a connection.</p>"
        )
        return view

    def _notices_tab(self) -> QTextBrowser:
        view = self._view()
        view.setAccessibleName("Third-party notices")
        notices = "".join(
            f"<p style='color:{d.TEXT_SECONDARY}'>{notice}</p>" for notice in REQUIRED_NOTICES
        )
        files = _licence_files()
        listing = (
            "".join(
                f"<li style='font-family:{d.FONT_MONO};color:{d.TEXT_PRIMARY}'>{path.name}</li>"
                for path in files
            )
            if files
            else f"<li style='color:{d.TEXT_MUTED}'>Licence texts are installed with the "
            "release package, in its <code>licenses</code> folder.</li>"
        )
        view.setHtml(
            f"<div style='font-size:{d.TYPE_TITLE}pt;font-weight:600;color:{d.TEXT_PRIMARY}'>"
            "Third-party notices</div>"
            f"{notices}"
            f"<p style='color:{d.TEXT_SECONDARY};margin-top:14px'>The full licence texts, the "
            "exact build configuration of the bundled FFmpeg, and the complete dependency "
            "manifest are installed alongside the application.</p>"
            f"<p style='color:{d.TEXT_SECONDARY}'>The corresponding source code for the "
            "FFmpeg libraries distributed with this product, together with the build "
            "configuration used to produce them, is available at:</p>"
            f"<p style='font-family:{d.FONT_MONO};color:{d.ACCENT}'>{SOURCE_URL}</p>"
            f"<div style='color:{d.TEXT_SECONDARY};font-weight:600;margin-top:18px'>"
            "Installed licence texts</div>"
            f"<ul>{listing}</ul>"
        )
        return view


def _link_row(label: str, url: str) -> str:
    return (
        f"<tr><td style='color:{d.TEXT_SECONDARY};padding-right:16px'>{label}</td>"
        f"<td style='font-family:{d.FONT_MONO};color:{d.ACCENT}'>{url}</td></tr>"
    )
