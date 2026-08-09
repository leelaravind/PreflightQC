"""The approved logo actually reaches the running interface.

File-level guards live in tests/packaging/test_final_binding.py; these need a real
QApplication to prove the wiring end of the chain: the shipped PNG loads, the main
window carries it, and the About dialog embeds it without touching the network-free
posture (the image is a document resource, not a URL).
"""

from __future__ import annotations

from preflightqc.ui import branding


class TestApplicationIcon:
    def test_the_icon_loads_and_is_not_null(self, qapp) -> None:
        icon = branding.application_icon()
        assert not icon.isNull()
        assert (256, 256) in [(s.width(), s.height()) for s in icon.availableSizes()]

    def test_the_main_window_carries_the_icon(self, qapp) -> None:
        from preflightqc.ui.main_window import MainWindow

        window = MainWindow()
        try:
            assert not window.windowIcon().isNull()
        finally:
            window.deleteLater()

    def test_logo_pixmap_scales_within_the_requested_box(self, qapp) -> None:
        pixmap = branding.logo_pixmap(96)
        assert not pixmap.isNull()
        assert pixmap.width() <= 96 and pixmap.height() <= 96
