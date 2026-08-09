"""The application icon, resolved from the shipped brand asset.

One asset, one loader. The PNG at ``assets/preflightqc.png`` is a pure resize of the
Product Owner-approved logo (``assets/logo/PROVENANCE.md`` at the repository root);
the executable and installer use the matching multi-size ``.ico``. Loading is
tolerant: a missing icon degrades to a null QIcon and the application runs unbranded
rather than refusing to start over artwork.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon, QPixmap

#: Shipped inside the package (declared in packaging/preflightqc.spec `datas`), so the
#: same relative path works from source and from the frozen `_internal/` layout.
ICON_PATH = Path(__file__).resolve().parent / "assets" / "preflightqc.png"


def application_icon() -> QIcon:
    """The window/taskbar icon, or a null icon if the asset is absent."""
    return QIcon(str(ICON_PATH)) if ICON_PATH.is_file() else QIcon()


def logo_pixmap(edge: int) -> QPixmap:
    """The logo scaled to fit an ``edge`` x ``edge`` box, for in-app surfaces."""
    pixmap = QPixmap(str(ICON_PATH))
    if pixmap.isNull():
        return pixmap
    from PySide6.QtCore import Qt

    return pixmap.scaled(
        edge,
        edge,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
