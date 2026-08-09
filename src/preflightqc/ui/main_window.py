"""The main window.

The UI thread does no file I/O and starts no processes: it dispatches commands to a
worker and renders the snapshots that come back. That is what keeps the window
responsive while a thousand-file batch runs, and it is asserted by a test.

No platform name and no platform threshold appears anywhere in this package — all of it
comes from preset data (spec 11.1), enforced by an automated scan. No colour appears here
either; every value comes from `design.py` through `theme.py`, and that is also enforced.

Layout follows docs/design/UI-DESIGN-SPEC-V1.md: three toolbar groups in workflow order,
a persistent preset context strip, a filterable batch table, and a status readout that
replaces five loose footer counters.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from preflightqc import __product_name__, __publisher__, __version__
from preflightqc.orchestration.runner import (
    BatchProgress,
    BatchRunner,
    CancellationToken,
    InspectionCache,
    InspectionSettings,
)
from preflightqc.platform import binaries
from preflightqc.platform.paths import shipped_presets_dir, user_profiles_dir
from preflightqc.profiles import store as profile_store
from preflightqc.profiles.compiler import compile_profile
from preflightqc.reporting import export as export_module
from preflightqc.reporting.export import ExportFormat
from preflightqc.reporting.model import build_report
from preflightqc.results.aggregate import FileResult
from preflightqc.rules.document import PresetDocument
from preflightqc.rules.loader import load_catalog
from preflightqc.scan.enumerate import EnumerationOptions, enumerate_inputs
from preflightqc.ui import design as d
from preflightqc.ui import severity_style, viewmodels
from preflightqc.ui.about import AboutDialog
from preflightqc.ui.widgets import EmptyState, StatusReadout

#: Filter chips above the batch table. `None` means "no filter". The values are
#: *display* statuses, so the chips count what the table shows.
_FILTERS: tuple[tuple[str, str | None], ...] = (
    ("All", None),
    ("Fail", "FAIL"),
    ("Warning", "WARN"),
    ("Inconclusive", "INCONCLUSIVE"),
    ("Pass", "PASS"),
)


class ScanWorker(QThread):
    """Runs one batch off the UI thread."""

    result_ready = Signal(int, object)
    progress_changed = Signal(object)
    finished_batch = Signal(object)

    def __init__(
        self,
        runner: BatchRunner,
        paths: Sequence[Path],
        preset: PresetDocument,
        token: CancellationToken,
    ) -> None:
        super().__init__()
        self._runner = runner
        self._paths = list(paths)
        self._preset = preset
        self._token = token

    def run(self) -> None:
        outcome = self._runner.run(
            self._paths,
            self._preset,
            token=self._token,
            on_result=lambda index, result: self.result_ready.emit(index, result),
            on_progress=lambda progress: self.progress_changed.emit(progress),
        )
        self.finished_batch.emit(outcome)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{__product_name__} {__version__}")
        self.resize(d.DEFAULT_WINDOW_WIDTH, d.DEFAULT_WINDOW_HEIGHT)
        # Below this the toolbar clips. Audit finding F-36.
        self.setMinimumSize(d.MIN_WINDOW_WIDTH, d.MIN_WINDOW_HEIGHT)
        self.setAcceptDrops(True)

        self._paths: list[Path] = []
        self._results: dict[int, FileResult] = {}
        self._token: CancellationToken | None = None
        self._worker: ScanWorker | None = None
        self._outcome = None
        self._started_at: datetime | None = None
        self._cache = InspectionCache()
        self._filter: str | None = None
        self._row_of: dict[int, int] = {}

        self._startup = binaries.check_all()
        self._presets = self._load_presets()

        self._build_ui()
        self._refresh_table()
        self._on_preset_changed()
        if not self._startup.usable:
            self._show_startup_problem()

    # -- construction -------------------------------------------------------

    def _load_presets(self) -> tuple[PresetDocument, ...]:
        """Shipped presets, plus the user's saved custom profiles.

        Two shapes live in the profiles directory and both have to be read. A profile
        someone hand-authored as a preset document is loaded by `load_catalog`; a profile
        saved by the application is a `CustomProfile` and has to be compiled first.

        Only the first path existed. The compiler was written, tested and never called by
        the application, so a saved profile never reached the selector — the feature was
        complete apart from being unreachable.
        """
        shipped = load_catalog([shipped_presets_dir()])
        reserved = frozenset(p.preset_id for p in shipped.presets)
        catalog = load_catalog([user_profiles_dir()], reserved_ids=reserved)

        profiles, profile_errors = profile_store.load_all()
        compiled: list[PresetDocument] = []
        rejected: list[tuple[Path, str]] = list(profile_errors)
        seen = set(reserved) | {p.preset_id for p in catalog.presets}
        for profile in profiles:
            try:
                document = compile_profile(profile)
            except Exception as error:
                # One unreadable profile must not cost the user every other preset.
                rejected.append((Path(profile.profile_id), str(error)))
                continue
            if document.preset_id in seen:
                continue
            seen.add(document.preset_id)
            compiled.append(document)

        self._rejected = (*shipped.rejected, *catalog.rejected, *rejected)
        return (*shipped.presets, *catalog.presets, *compiled)

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(d.SPACE_LG, d.SPACE_LG, d.SPACE_LG, d.SPACE_LG)
        layout.setSpacing(d.SPACE_LG)

        layout.addWidget(self._build_toolbar())
        layout.addWidget(self._build_context_strip())
        layout.addWidget(self._build_splitter(), 1)
        layout.addWidget(self._build_footer())

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self._build_menu()
        self._set_status_message("Ready. Add files or drop them onto the window.")

    def _button(self, text: str, tooltip: str, accessible: str, slot) -> QPushButton:
        button = QPushButton(text)
        button.setToolTip(tooltip)
        button.setAccessibleName(accessible)
        button.setAccessibleDescription(tooltip)
        button.clicked.connect(slot)
        return button

    def _build_toolbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("Toolbar")
        bar.setFixedHeight(d.TOOLBAR_HEIGHT)
        row = QHBoxLayout(bar)
        row.setContentsMargins(d.SPACE_LG, d.SPACE_SM, d.SPACE_LG, d.SPACE_SM)
        row.setSpacing(d.SPACE_SM)

        identity = QVBoxLayout()
        identity.setSpacing(0)
        wordmark = QLabel(__product_name__)
        wordmark.setObjectName("Wordmark")
        publisher = QLabel(f"by {__publisher__}")
        publisher.setObjectName("Publisher")
        identity.addWidget(wordmark)
        identity.addWidget(publisher)
        row.addLayout(identity)
        row.addSpacing(d.SPACE_2XL)
        row.addWidget(self._divider())
        row.addSpacing(d.SPACE_2XL)

        # 1 — bring files in
        self._add_files_button = self._button(
            "&Add files…", "Add video files to the batch (Ctrl+O)", "Add files", self._on_add_files
        )
        self._add_folder_button = self._button(
            "Add f&older…",
            "Add every video in a folder, including sub-folders (Ctrl+Shift+O)",
            "Add folder",
            self._on_add_folder,
        )
        self._clear_button = self._button(
            "Clear", "Remove every file and result from the batch", "Clear batch", self._on_clear
        )
        row.addWidget(self._add_files_button)
        row.addWidget(self._add_folder_button)
        row.addWidget(self._clear_button)

        row.addSpacing(d.SPACE_2XL)
        row.addWidget(self._divider())
        row.addSpacing(d.SPACE_2XL)

        # 2 — choose the spec
        preset_label = QLabel("Preset")
        preset_label.setObjectName("FieldLabel")
        self._preset_box = QComboBox()
        self._preset_box.setMinimumWidth(300)
        self._preset_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._preset_box.setAccessibleName("Delivery preset")
        self._preset_box.setToolTip("The delivery specification your files are checked against")
        self._populate_presets()
        self._preset_box.currentIndexChanged.connect(self._on_preset_changed)
        row.addWidget(preset_label)
        row.addWidget(self._preset_box, 1)

        row.addSpacing(d.SPACE_2XL)
        row.addWidget(self._divider())
        row.addSpacing(d.SPACE_2XL)

        # 3 — check
        self._run_button = self._button(
            "&Run check", "Check every file against the selected preset (F5)", "Run check",
            self._on_run,
        )
        self._run_button.setObjectName("PrimaryAction")
        self._run_button.setDefault(True)
        self._cancel_button = self._button(
            "Cancel", "Stop the run and keep the results so far (Esc)", "Cancel run", self._on_cancel
        )
        self._cancel_button.setEnabled(False)
        row.addWidget(self._run_button)
        row.addWidget(self._cancel_button)
        return bar

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setStyleSheet(f"color: {d.BORDER_SUBTLE};")
        return line

    def _populate_presets(self) -> None:
        options = viewmodels.build_preset_options(self._presets)
        shipped = [o for o in options if not o.is_custom]
        custom = [o for o in options if o.is_custom]
        for option in shipped:
            self._preset_box.addItem(option.menu_label, option.preset_id)
        if custom:
            self._preset_box.insertSeparator(self._preset_box.count())
            for option in custom:
                self._preset_box.addItem(option.menu_label, option.preset_id)

    def _build_context_strip(self) -> QFrame:
        strip = QFrame()
        strip.setObjectName("ContextStrip")
        row = QHBoxLayout(strip)
        row.setContentsMargins(d.SPACE_LG, d.SPACE_SM, d.SPACE_LG, d.SPACE_SM)
        row.setSpacing(d.SPACE_MD)

        self._context_primary = QLabel("")
        self._context_primary.setObjectName("ContextPrimary")
        self._context_detail = QLabel("")
        self._context_detail.setObjectName("ContextDetail")
        self._context_caveats = QLabel("")
        self._context_caveats.setObjectName("ContextDetail")
        self._context_caveats.setTextFormat(Qt.TextFormat.RichText)

        row.addWidget(self._context_primary)
        row.addWidget(self._context_detail)
        row.addStretch(1)
        row.addWidget(self._context_caveats)
        return strip

    def _build_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(d.SPACE_SM)
        left_layout.addLayout(self._build_filter_row())

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Status", "File", "Result"])
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(d.ROW_HEIGHT)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setWordWrap(False)
        self._table.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        # The Result column carried the per-file summary and used to truncate to
        # "1 warning, 4 …". It now has a floor wide enough for the longest real summary.
        self._table.setColumnWidth(2, 250)
        header.setMinimumSectionSize(90)
        # Sorting is off by design: findings and files are already in a deterministic
        # order, and re-sorting would hide that. Filtering serves the same need safely.
        self._table.setSortingEnabled(False)
        self._table.setAccessibleName("Batch results")
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        self._empty_state = EmptyState()
        self._batch_stack = QStackedWidget()
        self._batch_stack.addWidget(self._empty_state)
        self._batch_stack.addWidget(self._table)
        left_layout.addWidget(self._batch_stack, 1)

        self._detail_tabs = QTabWidget()
        self._findings_view = QTextBrowser()
        self._findings_view.setOpenExternalLinks(False)
        self._findings_view.setAccessibleName("Findings for the selected file")
        self._metadata_view = QTextBrowser()
        self._metadata_view.setOpenExternalLinks(False)
        self._metadata_view.setAccessibleName("Metadata read from the selected file")
        self._detail_tabs.addTab(self._findings_view, "Findings")
        self._detail_tabs.addTab(self._metadata_view, "Metadata")
        self._show_detail_placeholder()

        splitter.addWidget(left)
        splitter.addWidget(self._detail_tabs)
        splitter.setStretchFactor(0, 58)
        splitter.setStretchFactor(1, 42)
        splitter.setSizes([700, 520])
        return splitter

    def _build_filter_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(d.SPACE_XS)
        label = QLabel("Show")
        label.setObjectName("FieldLabel")
        row.addWidget(label)

        self._filter_group = QButtonGroup(self)
        self._filter_group.setExclusive(True)
        self._filter_buttons: dict[str | None, QPushButton] = {}
        for text, status in _FILTERS:
            chip = QPushButton(text)
            chip.setObjectName("FilterChip")
            chip.setCheckable(True)
            chip.setChecked(status is None)
            chip.setAccessibleName(f"Show {text.lower()} files")
            chip.setToolTip(f"Show only {text.lower()} results" if status else "Show every file")
            chip.clicked.connect(lambda _checked, s=status: self._on_filter(s))
            self._filter_group.addButton(chip)
            self._filter_buttons[status] = chip
            row.addWidget(chip)
        row.addStretch(1)
        return row

    def _build_footer(self) -> QFrame:
        footer = QFrame()
        footer.setObjectName("Readout")
        row = QHBoxLayout(footer)
        row.setContentsMargins(d.SPACE_LG, d.SPACE_SM, d.SPACE_LG, d.SPACE_SM)
        row.setSpacing(d.SPACE_LG)

        self._count_label = QLabel("")
        self._count_label.setObjectName("FieldLabel")
        self._readout = StatusReadout()
        self._summary_label = QLabel("")
        self._summary_label.setTextFormat(Qt.TextFormat.RichText)

        self._progress = QProgressBar()
        self._progress.setTextVisible(True)
        self._progress.setAccessibleName("Check progress")
        self._progress.setVisible(False)
        self._progress.setMaximumWidth(220)

        self._export_csv_button = self._button(
            "Export &CSV…",
            "Write one row per finding to a CSV file (Ctrl+Shift+E)",
            "Export CSV",
            lambda: self._on_export(ExportFormat.CSV),
        )
        self._export_html_button = self._button(
            "&Export report…",
            "Write a self-contained HTML report you can send or print (Ctrl+E)",
            "Export report",
            lambda: self._on_export(ExportFormat.HTML),
        )
        self._set_export_enabled(False)

        row.addWidget(self._count_label)
        row.addWidget(self._readout, 1)
        row.addWidget(self._summary_label)
        row.addWidget(self._progress)
        row.addWidget(self._export_csv_button)
        row.addWidget(self._export_html_button)
        return footer

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        self._add_action(file_menu, "&Add files…", "Ctrl+O", self._on_add_files)
        self._add_action(file_menu, "Add f&older…", "Ctrl+Shift+O", self._on_add_folder)
        file_menu.addSeparator()
        self._add_action(file_menu, "Export &report…", "Ctrl+E", lambda: self._on_export(ExportFormat.HTML))
        self._add_action(file_menu, "Export &CSV…", "Ctrl+Shift+E", lambda: self._on_export(ExportFormat.CSV))
        file_menu.addSeparator()
        self._add_action(file_menu, "E&xit", "Alt+F4", self.close)

        check_menu = self.menuBar().addMenu("&Check")
        self._add_action(check_menu, "&Run check", "F5", self._on_run)
        self._add_action(check_menu, "&Cancel", "Esc", self._on_cancel)
        check_menu.addSeparator()
        self._add_action(check_menu, "C&lear batch", "Ctrl+W", self._on_clear)

        help_menu = self.menuBar().addMenu("&Help")
        self._add_action(help_menu, f"&About {__product_name__}", "F1", self._on_about)

    def _add_action(self, menu, text: str, shortcut: str, slot) -> QAction:
        action = QAction(text, self)
        action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    # -- input --------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 - Qt override
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 - Qt override
        paths = [
            Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()
        ]
        if paths:
            self._add_paths(paths)
            event.acceptProposedAction()

    @Slot()
    def _on_add_files(self) -> None:
        names, _ = QFileDialog.getOpenFileNames(self, "Add video files")
        if names:
            self._add_paths([Path(n) for n in names])

    @Slot()
    def _on_add_folder(self) -> None:
        name = QFileDialog.getExistingDirectory(self, "Add folder")
        if name:
            self._add_paths([Path(name)])

    def _add_paths(self, paths: Sequence[Path]) -> None:
        existing = set(self._paths)
        found = enumerate_inputs(paths, options=EnumerationOptions(recurse=True))
        added = [p for p in found.files if p not in existing]
        self._paths.extend(added)
        self._refresh_table()
        message = f"{len(added)} file(s) added."
        if found.skipped_duplicates:
            message += f" {found.skipped_duplicates} duplicate(s) skipped."
        if found.unreadable:
            message += f" {len(found.unreadable)} path(s) could not be read."
        self._set_status_message(message)

    @Slot()
    def _on_clear(self) -> None:
        self._paths.clear()
        self._results.clear()
        self._outcome = None
        self._refresh_table()
        self._show_detail_placeholder()
        self._readout.clear()
        self._summary_label.clear()
        self._set_export_enabled(False)
        self._set_status_message("Batch cleared.")

    @Slot()
    def _on_filter(self, status: str | None) -> None:
        self._filter = status
        self._apply_filter()

    def _display_rows(self) -> list[viewmodels.FileRow]:
        return [
            viewmodels.build_file_row(index, path, self._results.get(index))
            for index, path in enumerate(self._paths)
        ]

    def _apply_filter(self) -> None:
        for row in self._display_rows():
            position = self._row_of.get(row.index)
            if position is None:
                continue
            visible = (
                self._filter is None
                or (row.is_complete and row.display_status == self._filter)
            )
            self._table.setRowHidden(position, not visible)

    def _update_filter_counts(self) -> None:
        counts: dict[str, int] = {}
        for row in self._display_rows():
            if row.is_complete:
                counts[row.display_status] = counts.get(row.display_status, 0) + 1
        for text, status in _FILTERS:
            chip = self._filter_buttons[status]
            if status is None:
                chip.setText(f"All  {len(self._paths)}" if self._paths else "All")
            else:
                count = counts.get(status, 0)
                chip.setText(f"{text}  {count}" if count else text)
                chip.setEnabled(bool(count) or self._filter == status)

    # -- running ------------------------------------------------------------

    def _selected_preset(self) -> PresetDocument | None:
        preset_id = self._preset_box.currentData()
        return next((p for p in self._presets if p.preset_id == preset_id), None)

    @Slot()
    def _on_preset_changed(self) -> None:
        preset = self._selected_preset()
        if preset is None:
            return
        option = viewmodels.build_preset_options([preset])[0]
        self._context_primary.setText(option.menu_label)
        self._context_detail.setText(option.context_line)
        if option.caveats:
            tone = severity_style.for_severity("INFO")
            self._context_caveats.setText(
                f"<span style='{severity_style.badge_stylesheet(tone)}'>"
                f"i {len(option.caveats)} note(s)</span>"
            )
            self._context_caveats.setToolTip("\n\n".join(f"• {c}" for c in option.caveats))
            self._context_caveats.setAccessibleDescription(" ".join(option.caveats))
        else:
            self._context_caveats.clear()
            self._context_caveats.setToolTip("")

    @Slot()
    def _on_run(self) -> None:
        preset = self._selected_preset()
        if preset is None or not self._paths:
            self._set_status_message("Add files and choose a preset first.")
            return
        if not self._startup.usable:
            self._show_startup_problem()
            return

        self._results.clear()
        self._outcome = None
        self._started_at = datetime.now().astimezone()
        self._token = CancellationToken()
        runner = BatchRunner(
            startup=self._startup, settings=InspectionSettings(), cache=self._cache
        )

        self._worker = ScanWorker(runner, self._paths, preset, self._token)
        self._worker.result_ready.connect(self._on_result)
        self._worker.progress_changed.connect(self._on_progress)
        self._worker.finished_batch.connect(self._on_batch_finished)

        self._set_running(True)
        self._progress.setVisible(True)
        self._progress.setRange(0, len(self._paths))
        self._progress.setValue(0)
        self._progress.setFormat(f"0 of {len(self._paths)}")
        self._set_status_message("Checking…")
        self._worker.start()

    @Slot()
    def _on_cancel(self) -> None:
        if self._token is not None:
            self._token.cancel()
            self._set_status_message("Cancelling — results so far will be kept.")

    @Slot(int, object)
    def _on_result(self, index: int, result: FileResult) -> None:
        self._results[index] = result
        self._update_row(index)
        self._update_filter_counts()

    @Slot(object)
    def _on_progress(self, progress: BatchProgress) -> None:
        self._progress.setValue(progress.completed)
        self._progress.setFormat(f"{progress.completed} of {progress.total}")

    @Slot(object)
    def _on_batch_finished(self, outcome) -> None:
        self._outcome = outcome
        self._set_running(False)
        self._progress.setVisible(False)
        self._render_summary(outcome)
        self._set_export_enabled(True)
        self._update_filter_counts()
        self._select_most_severe_row()
        if outcome.cancelled:
            self._set_status_message("Cancelled. Partial results are shown and can be exported.")
        else:
            self._set_status_message("Check complete.")

    def _render_summary(self, outcome) -> None:
        rows = self._display_rows()
        segments = viewmodels.build_readout_segments(rows)
        self._readout.set_segments(segments)
        self._count_label.setText(f"{outcome.summary.total_files} files")
        chips = []
        for name, count in segments:
            if not count:
                continue
            tone = severity_style.for_status(name)
            chips.append(
                f"<span style='{severity_style.badge_stylesheet(tone)}'>"
                f"{tone.marker} {count} {tone.label}</span>"
            )
        self._summary_label.setText("&nbsp;&nbsp;".join(chips))

    def _select_most_severe_row(self) -> None:
        """Open the detail pane on the thing most worth reading.

        Leaving nothing selected meant a finished batch showed an empty detail pane, and
        the first failure — the reason the user ran the check — was one unhinted click
        away. Audit finding F-14.
        """
        ranking = {name: rank for rank, name in enumerate(viewmodels.READOUT_ORDER)}
        best: tuple[int, int] | None = None
        for row in self._display_rows():
            if not row.is_complete:
                continue
            rank = ranking.get(row.display_status, len(ranking))
            if best is None or rank < best[0]:
                best = (rank, row.index)
        if best is None:
            return
        position = self._row_of.get(best[1])
        if position is not None:
            self._table.selectRow(position)

    def _set_running(self, running: bool) -> None:
        self._run_button.setEnabled(not running)
        self._cancel_button.setEnabled(running)
        self._add_files_button.setEnabled(not running)
        self._add_folder_button.setEnabled(not running)
        self._clear_button.setEnabled(not running)
        self._preset_box.setEnabled(not running)

    def _set_export_enabled(self, enabled: bool) -> None:
        self._export_csv_button.setEnabled(enabled)
        self._export_html_button.setEnabled(enabled)

    # -- rendering ----------------------------------------------------------

    def _refresh_table(self) -> None:
        self._table.setRowCount(len(self._paths))
        self._row_of = {index: index for index in range(len(self._paths))}
        for index in range(len(self._paths)):
            self._update_row(index)
        self._batch_stack.setCurrentWidget(self._table if self._paths else self._empty_state)
        self._update_filter_counts()

    def _update_row(self, index: int) -> None:
        row = viewmodels.build_file_row(index, self._paths[index], self._results.get(index))
        tone = severity_style.for_status(row.display_status) if row.is_complete else None

        status_item = QTableWidgetItem(tone.chip_text if tone else "· Queued")
        if tone is not None:
            status_item.setForeground(QBrush(QColor(tone.foreground)))
            if row.is_inconclusive:
                status_item.setToolTip(viewmodels.FileRow.INCONCLUSIVE_REASON)
        name_item = QTableWidgetItem(row.name)
        name_item.setToolTip(row.path)
        result_item = QTableWidgetItem(row.summary_text)
        result_item.setToolTip(row.failure_hint or row.summary_text)

        for column, item in enumerate((status_item, name_item, result_item)):
            item.setData(Qt.ItemDataRole.UserRole, index)
            self._table.setItem(index, column, item)

        # A screen reader reads the row, so the row must carry the verdict.
        label = tone.label if tone else "Queued"
        name_item.setData(
            Qt.ItemDataRole.AccessibleDescriptionRole,
            f"{label}. {row.summary_text}",
        )

    @Slot()
    def _on_selection_changed(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        item = self._table.item(rows[0].row(), 0)
        index = item.data(Qt.ItemDataRole.UserRole) if item is not None else rows[0].row()
        result = self._results.get(index)
        if result is None:
            self._show_detail_placeholder("This file has not been checked yet.")
            return
        detail = viewmodels.build_file_detail(result)
        self._findings_view.setHtml(_render_findings(detail))
        self._metadata_view.setHtml(_render_metadata(detail))

    def _show_detail_placeholder(self, message: str = "") -> None:
        text = message or "Select a file to see what was checked and what was found."
        self._findings_view.setHtml(
            f"<p style='color:{d.TEXT_MUTED}'>{text}</p>"
        )
        self._metadata_view.setHtml(
            f"<p style='color:{d.TEXT_MUTED}'>"
            "Metadata read from the file appears here once it has been checked.</p>"
        )

    def _set_status_message(self, message: str) -> None:
        self.statusBar().showMessage(message)

    # -- export -------------------------------------------------------------

    @Slot()
    def _on_export(self, fmt: ExportFormat) -> None:
        preset = self._selected_preset()
        if self._outcome is None or preset is None or self._started_at is None:
            self._set_status_message("Run a check before exporting.")
            return
        report = build_report(
            results=self._outcome.results,
            summary=self._outcome.summary,
            preset=preset,
            product_version=__version__,
            scan_started=self._started_at,
            scan_finished=datetime.now().astimezone(),
            inspector_versions=self._startup.versions(),
        )
        default_dir = export_module.default_output_dir()
        default_dir.mkdir(parents=True, exist_ok=True)
        suggested = default_dir / export_module.suggested_filename(report, fmt)
        chosen, _ = QFileDialog.getSaveFileName(
            self,
            "Export report",
            str(suggested),
            "CSV (*.csv)" if fmt is ExportFormat.CSV else "HTML report (*.html)",
        )
        if not chosen:
            return
        result = export_module.export(report, Path(chosen), fmt)
        if result.ok:
            self._set_status_message("Exported " + ", ".join(p.name for p in result.written))
        else:
            QMessageBox.warning(self, "Export failed", f"{result.error}\n\n{result.hint}")

    # -- dialogs ------------------------------------------------------------

    @Slot()
    def _on_about(self) -> None:
        AboutDialog(self._startup, parent=self).exec()

    def _show_startup_problem(self) -> None:
        QMessageBox.critical(
            self,
            "Inspection tools unavailable",
            "PreflightQC could not start its bundled inspection tools, so it cannot "
            "check any files.\n\n" + "\n\n".join(self._startup.problems()),
        )

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        """Cancel and reap before exiting, so no inspector process is orphaned."""
        if self._token is not None:
            self._token.cancel()
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(5000)
        event.accept()


# ---------------------------------------------------------------------------
# Rich-text rendering
# ---------------------------------------------------------------------------


def _card(body: str, *, background: str, accent: str) -> str:
    """One block with a real background and a severity edge.

    Qt's rich-text engine renders `<div>` backgrounds inconsistently — a styled div
    paints behind its text lines rather than behind the block, which produced banded
    stripes instead of cards. A one-cell table is the construct Qt does paint reliably,
    so the blocks are tables. This is a Qt limitation, not a design choice.
    """
    return (
        f"<table width='100%' cellspacing='0' cellpadding='0' "
        f"style='margin:0 0 10px 0'><tr>"
        f"<td width='3' bgcolor='{accent}'></td>"
        f"<td bgcolor='{background}' style='padding:10px 12px'>{body}</td>"
        f"</tr></table>"
    )


def _render_findings(detail: viewmodels.FileDetail) -> str:
    tone = severity_style.for_status(
        "INCONCLUSIVE" if detail.is_inconclusive else detail.status
    )
    header = (
        f"<p style='margin:0 0 10px 0'>"
        f"<span style='{severity_style.badge_stylesheet(tone)}'>"
        f"{tone.marker} {tone.label}</span>"
        f"<span style='color:{d.TEXT_SECONDARY}'>&nbsp;&nbsp;{detail.passed_summary}</span>"
        f"</p>"
    )

    if detail.is_inconclusive:
        header += _card(
            f"<span style='color:{d.TEXT_PRIMARY}'>"
            f"{viewmodels.FileRow.INCONCLUSIVE_REASON}</span>",
            background=d.UNKNOWN_TONE.background,
            accent=d.UNKNOWN_TONE.foreground,
        )

    if not detail.findings:
        # "Every rule was satisfied" is only true if rules actually ran. Saying it about
        # a file nothing could be read from would contradict the banner directly above.
        message = (
            "Every rule in this preset was satisfied."
            if detail.checks_total
            else "No rule in this preset could be evaluated against this file."
        )
        return header + f"<p style='color:{d.TEXT_SECONDARY}'>{message}</p>"

    parts = [header]
    for finding in detail.findings:
        style = severity_style.for_severity(finding.severity)
        unknown = (
            f"<p style='color:{d.TEXT_MUTED};margin:6px 0 0 0'>"
            f"Not evaluated: {finding.unknown_reason}</p>"
            if finding.unknown_reason
            else ""
        )
        provenance = (
            f"<span style='font-family:{d.FONT_MONO}'>{finding.provenance}</span>&nbsp;·&nbsp;"
            if finding.provenance
            else ""
        )
        body = (
            f"<table width='100%' cellpadding='0' cellspacing='0'><tr>"
            f"<td><span style='{severity_style.badge_stylesheet(style)}'>"
            f"{style.marker} {style.label}</span>"
            f"&nbsp;&nbsp;<b style='font-size:{d.TYPE_HEADING}pt'>{finding.property_label}</b></td>"
            f"<td align='right'><span style='color:{d.TEXT_MUTED};font-size:{d.TYPE_CAPTION}pt'>"
            f"{finding.classification_label}</span></td></tr></table>"
            f"<table cellpadding='1' cellspacing='0' style='margin-top:6px'>"
            f"<tr><td width='110' style='color:{d.TEXT_SECONDARY}'>Detected</td>"
            f"<td style='font-family:{d.FONT_MONO};color:{d.TEXT_PRIMARY}'>"
            f"{finding.detected}</td></tr>"
            f"<tr><td style='color:{d.TEXT_SECONDARY}'>{finding.expectation_label}</td>"
            f"<td style='font-family:{d.FONT_MONO};color:{d.TEXT_PRIMARY}'>"
            f"{finding.expected}</td></tr></table>"
            f"<p style='margin:8px 0 0 0;color:{d.TEXT_PRIMARY}'>{finding.explanation}</p>"
            f"{unknown}"
            f"<p style='margin:8px 0 0 0;color:{d.TEXT_MUTED};font-size:{d.TYPE_CAPTION}pt'>"
            f"{provenance}<span style='font-family:{d.FONT_MONO}'>{finding.rule_id}</span>"
            f"<br>{finding.source_title} · verified {finding.source_access_date} · "
            f"confidence {finding.source_confidence}</p>"
        )
        parts.append(_card(body, background=d.SURFACE_RAISED, accent=style.foreground))
    parts.append(
        f"<p style='color:{d.TEXT_MUTED};font-size:{d.TYPE_CAPTION}pt;margin-top:12px'>"
        "Full source URLs for every rule are included in the exported report.</p>"
    )
    return "".join(parts)


_STATE_LEGEND = (
    "Known — read from the file · "
    "Not present — the file does not carry it · "
    "Not determined — PreflightQC could not read it"
)

_STATE_LABELS = {
    "KNOWN": "Known",
    "NOT_PRESENT": "Not present",
    "UNDETERMINED": "Not determined",
    "CONFLICTED": "Inspectors disagree",
}


def _render_metadata(detail: viewmodels.FileDetail) -> str:
    if not detail.metadata:
        return f"<p style='color:{d.TEXT_MUTED}'>No metadata could be read from this file.</p>"

    # One table for the whole pane, with group headings as spanning rows. Opening a new
    # table per group left unbalanced tags in Qt's renderer and collapsed the columns
    # until a value wrapped one character per line.
    parts = [
        f"<p style='color:{d.TEXT_MUTED};font-size:{d.TYPE_CAPTION}pt;margin:0 0 10px 0'>"
        f"{_STATE_LEGEND}</p>",
        "<table width='100%' cellpadding='3' cellspacing='0'>",
    ]
    current = ""
    for row in detail.metadata:
        if row.group != current:
            current = row.group
            parts.append(
                f"<tr><td colspan='3' style='color:{d.TEXT_SECONDARY};font-weight:600;"
                f"font-size:{d.TYPE_LABEL}pt;padding-top:12px'>{current.upper()}</td></tr>"
            )
        known = row.state == "KNOWN"
        colour = d.TEXT_PRIMARY if known else d.TEXT_MUTED
        state_label = _STATE_LABELS.get(row.state, row.state.title())
        value = row.value if known else "—"
        parts.append(
            f"<tr><td width='42%' style='color:{d.TEXT_SECONDARY}'>{row.label}</td>"
            f"<td width='36%' style='font-family:{d.FONT_MONO};color:{colour}'>{value}</td>"
            f"<td width='22%' style='color:{d.TEXT_MUTED};font-size:{d.TYPE_CAPTION}pt'>"
            f"{state_label}</td></tr>"
        )
    parts.append("</table>")

    if detail.diagnostics:
        parts.append(
            f"<div style='margin-top:14px;color:{d.TEXT_SECONDARY};"
            f"font-size:{d.TYPE_CAPTION}pt'>"
            + "".join(f"<p>{note}</p>" for note in detail.diagnostics)
            + "</div>"
        )
    return "".join(parts)
