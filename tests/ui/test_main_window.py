"""Widget-level tests: the things that need a real QApplication to be true.

Accessibility is the reason most of these exist. An accessible name is not visible in a
screenshot and not visible in a code review — the only way to know every control has one
is to walk the widget tree and ask.

Marked `ui` so a headless environment can deselect them; everything that can be tested
without Qt lives in `test_presentation.py` instead.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QComboBox, QPushButton, QTableWidget, QTextBrowser

from preflightqc import LEGAL_URL, SOURCE_URL, SUPPORT_URL, __publisher__
from preflightqc.ui import design
from preflightqc.ui.about import AboutDialog
from preflightqc.ui.main_window import MainWindow
from preflightqc.ui.theme import apply_theme, build_palette, style_sheet
from preflightqc.ui.widgets import EmptyState, StatusReadout

pytestmark = pytest.mark.ui


@pytest.fixture(scope="module")
def themed_app(qapp):
    apply_theme(qapp)
    return qapp


@pytest.fixture
def window(themed_app, qtbot) -> MainWindow:
    main = MainWindow()
    qtbot.addWidget(main)
    return main


class TestTheme:
    def test_the_style_sheet_builds_from_tokens(self) -> None:
        sheet = style_sheet()
        assert design.SURFACE_BASE in sheet
        assert design.ACCENT in sheet
        assert design.FONT_MONO in sheet

    def test_anything_that_suppresses_an_outline_replaces_it(self) -> None:
        """`outline: none` is only acceptable where something else shows focus.

        The item views drop Qt's dotted item rectangle because they use full-row
        selection, which is a stronger indicator — but only if the view itself also
        shows that it holds focus. Asserting the string never appears would be easy and
        wrong; asserting the replacement exists is the invariant that matters.
        """
        sheet = style_sheet()
        suppressors = ("QTableWidget", "QTableView", "QComboBox QAbstractItemView")
        for widget in suppressors:
            assert "outline: none" in sheet or "outline:none" in sheet
            assert widget in sheet
        for focusable in ("QTableWidget:focus", "QTableView:focus", "QComboBox:focus"):
            assert focusable in sheet

    def test_every_focusable_control_declares_a_focus_treatment(self) -> None:
        sheet = style_sheet()
        for selector in ("QPushButton:focus", "QComboBox:focus", "QTextBrowser:focus"):
            assert selector in sheet

    def test_the_focus_ring_uses_the_accent_and_a_real_width(self) -> None:
        sheet = style_sheet()
        assert f"outline: {design.FOCUS_RING_WIDTH}px solid {design.ACCENT}" in sheet

    def test_the_palette_covers_disabled_text(self, themed_app) -> None:
        """Disabled must read as inert, never as invisible."""
        from PySide6.QtGui import QPalette

        palette = build_palette()
        disabled = palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText)
        assert disabled.name().lower() == design.TEXT_MUTED.lower()


class TestWindowShell:
    def test_the_window_cannot_be_resized_until_the_toolbar_clips(
        self, window: MainWindow
    ) -> None:
        assert window.minimumWidth() == design.MIN_WINDOW_WIDTH
        assert window.minimumHeight() == design.MIN_WINDOW_HEIGHT

    def test_it_opens_on_the_empty_state_not_a_blank_table(self, window: MainWindow) -> None:
        assert isinstance(window._batch_stack.currentWidget(), EmptyState)

    def test_the_empty_state_names_the_three_steps(self, window: MainWindow) -> None:
        assert len(EmptyState.STEPS) == 3
        assert "read-only" in EmptyState.PRIVACY

    def test_the_publisher_is_visible_in_the_shell(self, window: MainWindow) -> None:
        from PySide6.QtWidgets import QLabel

        texts = [label.text() for label in window.findChildren(QLabel)]
        assert any(__publisher__ in text for text in texts)

    def test_export_is_disabled_until_there_is_something_to_export(
        self, window: MainWindow
    ) -> None:
        assert not window._export_csv_button.isEnabled()
        assert not window._export_html_button.isEnabled()

    def test_the_preset_selector_is_populated(self, window: MainWindow) -> None:
        assert window._preset_box.count() >= 12

    def test_no_preset_label_repeats_its_platform(self, window: MainWindow) -> None:
        """Audit F-9, asserted against the widget a user actually reads."""
        for index in range(window._preset_box.count()):
            text = window._preset_box.itemText(index)
            if not text:
                continue  # separator
            head = text.split(" — ")[0]
            assert not text.startswith(f"{head} — {head} — "), text

    def test_the_context_strip_shows_the_active_preset_and_its_date(
        self, window: MainWindow
    ) -> None:
        assert window._context_primary.text()
        assert "verified" in window._context_detail.text()


class TestCustomProfilesReachTheSelector:
    """A saved profile used to be invisible: the compiler was never called.

    `compile_profile` had tests and no caller in the application, so a user could save a
    custom delivery specification and never see it again. The store, the compiler and the
    export/import were all complete; the one line that joined them to the interface was
    missing.
    """

    @pytest.fixture
    def profile_dir(self, tmp_path, monkeypatch):
        from preflightqc.platform import paths
        from preflightqc.profiles import store
        from preflightqc.profiles.model import CustomProfile, ProfileProperty, PropertySpec

        directory = tmp_path / "profiles"
        directory.mkdir()
        monkeypatch.setattr(paths, "user_profiles_dir", lambda: directory)
        monkeypatch.setattr(store, "user_profiles_dir", lambda: directory, raising=False)

        profile = CustomProfile(
            profile_id=store.new_profile_id(),
            name="Client house spec",
            client="Example Client",
            properties={ProfileProperty.WIDTH: PropertySpec(exact=1920.0)},
        )
        store.save(profile, directory=directory)
        return directory

    def test_a_saved_profile_appears_in_the_selector(
        self, themed_app, qtbot, profile_dir, monkeypatch
    ) -> None:
        import preflightqc.ui.main_window as module

        monkeypatch.setattr(module, "user_profiles_dir", lambda: profile_dir)
        window = MainWindow()
        qtbot.addWidget(window)
        labels = [
            window._preset_box.itemText(i) for i in range(window._preset_box.count())
        ]
        assert any("Client house spec" in label for label in labels)

    def test_it_is_grouped_apart_from_the_shipped_presets(
        self, themed_app, qtbot, profile_dir, monkeypatch
    ) -> None:
        import preflightqc.ui.main_window as module

        monkeypatch.setattr(module, "user_profiles_dir", lambda: profile_dir)
        window = MainWindow()
        qtbot.addWidget(window)
        labels = [
            window._preset_box.itemText(i) for i in range(window._preset_box.count())
        ]
        # A separator renders as an empty entry; the custom profile must be after it.
        assert "" in labels
        assert labels.index("") < next(
            i for i, label in enumerate(labels) if "Client house spec" in label
        )

    def test_a_broken_profile_does_not_stop_the_window_opening(
        self, themed_app, qtbot, profile_dir, monkeypatch
    ) -> None:
        """One unreadable profile must not cost the user every other preset."""
        import preflightqc.ui.main_window as module

        (profile_dir / "broken.json").write_text("{ not json", encoding="utf-8")
        monkeypatch.setattr(module, "user_profiles_dir", lambda: profile_dir)
        window = MainWindow()
        qtbot.addWidget(window)
        assert window._preset_box.count() >= 12


class TestAccessibleNames:
    """Audit F-33: a screen reader announced "button" for the primary action."""

    def test_every_button_has_an_accessible_name(self, window: MainWindow) -> None:
        unnamed = [
            button.text()
            for button in window.findChildren(QPushButton)
            if not button.accessibleName()
        ]
        assert unnamed == []

    def test_every_button_has_a_tooltip(self, window: MainWindow) -> None:
        untipped = [
            button.text() for button in window.findChildren(QPushButton) if not button.toolTip()
        ]
        assert untipped == []

    def test_the_preset_selector_is_named(self, window: MainWindow) -> None:
        for box in window.findChildren(QComboBox):
            assert box.accessibleName()

    def test_the_table_and_detail_views_are_named(self, window: MainWindow) -> None:
        for table in window.findChildren(QTableWidget):
            assert table.accessibleName()
        for view in window.findChildren(QTextBrowser):
            assert view.accessibleName()

    def test_the_readout_describes_itself_when_empty(self, themed_app, qtbot) -> None:
        readout = StatusReadout()
        qtbot.addWidget(readout)
        assert "No files checked" in readout.accessibleDescription()

    def test_the_readout_describes_its_counts(self, themed_app, qtbot) -> None:
        readout = StatusReadout()
        qtbot.addWidget(readout)
        readout.set_segments((("FAIL", 2), ("WARN", 1), ("PASS", 0)))
        description = readout.accessibleDescription()
        assert "2 fail" in description
        assert "1 warning" in description
        assert "0 pass" not in description


class TestKeyboard:
    """Audit F-35: there were no mnemonics and no shortcuts."""

    def test_the_main_actions_carry_mnemonics(self, window: MainWindow) -> None:
        labelled = [b.text() for b in window.findChildren(QPushButton) if "&" in b.text()]
        assert len(labelled) >= 4

    def test_the_menus_expose_the_workflow_with_shortcuts(self, window: MainWindow) -> None:
        shortcuts = {
            action.shortcut().toString()
            for menu in window.menuBar().findChildren(type(window.menuBar().actions()[0].menu()))
            for action in menu.actions()
            if not action.shortcut().isEmpty()
        }
        assert {"F5", "Ctrl+O", "Ctrl+E"} <= shortcuts


class TestAboutDialog:
    @pytest.fixture
    def about(self, window: MainWindow, qtbot) -> AboutDialog:
        dialog = AboutDialog(window._startup, parent=window)
        qtbot.addWidget(dialog)
        return dialog

    @staticmethod
    def _notices_html(about: AboutDialog) -> str:
        """Select the notices view by name; child order is not a contract."""
        view = next(
            v
            for v in about.findChildren(QTextBrowser)
            if v.accessibleName() == "Third-party notices"
        )
        return view.toHtml()

    def test_it_never_opens_a_link_itself(self, about: AboutDialog) -> None:
        """Displaying a URL must not become the reason a no-network product connects."""
        for view in about.findChildren(QTextBrowser):
            assert not view.openExternalLinks()

    def test_it_names_the_publisher(self, about: AboutDialog) -> None:
        html = "".join(view.toHtml() for view in about.findChildren(QTextBrowser))
        assert __publisher__ in html

    def test_it_shows_the_support_legal_and_source_locations(self, about: AboutDialog) -> None:
        html = "".join(view.toHtml() for view in about.findChildren(QTextBrowser))
        for url in (SUPPORT_URL, LEGAL_URL, SOURCE_URL):
            assert url in html

    def test_the_corresponding_source_location_is_stated(self, about: AboutDialog) -> None:
        """An LGPL obligation that only appears online would not be a notice."""
        notices = self._notices_html(about)
        assert SOURCE_URL in notices

    def test_the_required_notices_are_present(self, about: AboutDialog) -> None:
        from preflightqc.ui.about import REQUIRED_NOTICES

        notices = self._notices_html(about)
        for required in REQUIRED_NOTICES:
            # Qt re-wraps text, so compare on a distinctive fragment rather than the
            # whole sentence.
            assert required.split(",")[0][:40] in notices.replace("\n", " ")

    def test_it_states_the_lgpl_version_the_build_is_actually_under(
        self, about: AboutDialog
    ) -> None:
        notices = self._notices_html(about)
        assert "LGPLv3" in notices
