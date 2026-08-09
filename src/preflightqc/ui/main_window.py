"""The main window.

The UI thread does no file I/O and starts no processes: it dispatches commands to a
worker and renders the snapshots that come back. That is what keeps the window
responsive while a thousand-file batch runs, and it is asserted by a test.

No platform name and no platform threshold appears anywhere in this package — all of it
comes from preset data (spec 11.1), enforced by an automated scan.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from preflightqc import __product_name__, __version__
from preflightqc.orchestration.runner import (
    BatchProgress,
    BatchRunner,
    CancellationToken,
    InspectionCache,
    InspectionSettings,
)
from preflightqc.platform import binaries
from preflightqc.platform.paths import shipped_presets_dir, user_profiles_dir
from preflightqc.reporting import export as export_module
from preflightqc.reporting.export import ExportFormat
from preflightqc.reporting.model import build_report
from preflightqc.results.aggregate import FileResult
from preflightqc.rules.document import PresetDocument
from preflightqc.rules.loader import load_catalog
from preflightqc.scan.enumerate import EnumerationOptions, enumerate_inputs
from preflightqc.ui import severity_style, viewmodels
from preflightqc.ui.about import AboutDialog


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
        self.resize(1180, 780)
        self.setAcceptDrops(True)

        self._paths: list[Path] = []
        self._results: dict[int, FileResult] = {}
        self._token: CancellationToken | None = None
        self._worker: ScanWorker | None = None
        self._outcome = None
        self._started_at: datetime | None = None
        self._cache = InspectionCache()

        self._startup = binaries.check_all()
        self._presets = self._load_presets()

        self._build_ui()
        self._refresh_table()
        if not self._startup.usable:
            self._show_startup_problem()

    # -- construction -------------------------------------------------------

    def _load_presets(self) -> tuple[PresetDocument, ...]:
        shipped = load_catalog([shipped_presets_dir()])
        reserved = frozenset(p.preset_id for p in shipped.presets)
        custom = load_catalog([user_profiles_dir()], reserved_ids=reserved)
        self._rejected = (*shipped.rejected, *custom.rejected)
        return (*shipped.presets, *custom.presets)

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addLayout(self._build_toolbar())
        layout.addWidget(self._build_splitter(), 1)
        layout.addLayout(self._build_footer())

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self._build_menu()
        self._set_status_message("Drop video files or folders here to begin.")

    def _build_toolbar(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self._add_files_button = QPushButton("Add files…")
        self._add_files_button.clicked.connect(self._on_add_files)
        self._add_folder_button = QPushButton("Add folder…")
        self._add_folder_button.clicked.connect(self._on_add_folder)
        self._clear_button = QPushButton("Clear")
        self._clear_button.clicked.connect(self._on_clear)

        self._preset_box = QComboBox()
        self._preset_box.setMinimumWidth(320)
        for option in viewmodels.build_preset_options(self._presets):
            self._preset_box.addItem(
                f"{option.platform} — {option.display_name}", option.preset_id
            )
        self._preset_box.currentIndexChanged.connect(self._on_preset_changed)

        self._run_button = QPushButton("Run check")
        self._run_button.setDefault(True)
        self._run_button.clicked.connect(self._on_run)
        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setEnabled(False)
        self._cancel_button.clicked.connect(self._on_cancel)

        row.addWidget(self._add_files_button)
        row.addWidget(self._add_folder_button)
        row.addWidget(self._clear_button)
        row.addSpacing(16)
        row.addWidget(QLabel("Preset:"))
        row.addWidget(self._preset_box, 1)
        row.addSpacing(16)
        row.addWidget(self._run_button)
        row.addWidget(self._cancel_button)
        return row

    def _build_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Status", "File", "Result"])
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # Sorting is off by design: findings and files are already in a deterministic
        # order, and re-sorting would hide that.
        self._table.setSortingEnabled(False)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        self._detail_tabs = QTabWidget()
        self._findings_view = QTextBrowser()
        self._findings_view.setOpenExternalLinks(False)
        self._metadata_view = QTextBrowser()
        self._metadata_view.setOpenExternalLinks(False)
        self._detail_tabs.addTab(self._findings_view, "Findings")
        self._detail_tabs.addTab(self._metadata_view, "Metadata")

        splitter.addWidget(self._table)
        splitter.addWidget(self._detail_tabs)
        splitter.setSizes([560, 620])
        return splitter

    def _build_footer(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self._progress = QProgressBar()
        self._progress.setTextVisible(True)
        self._summary_label = QLabel("")
        self._export_csv_button = QPushButton("Export CSV…")
        self._export_csv_button.setEnabled(False)
        self._export_csv_button.clicked.connect(lambda: self._on_export(ExportFormat.CSV))
        self._export_html_button = QPushButton("Export report…")
        self._export_html_button.setEnabled(False)
        self._export_html_button.clicked.connect(lambda: self._on_export(ExportFormat.HTML))

        row.addWidget(self._progress, 1)
        row.addWidget(self._summary_label)
        row.addWidget(self._export_csv_button)
        row.addWidget(self._export_html_button)
        return row

    def _build_menu(self) -> None:
        help_menu = self.menuBar().addMenu("&Help")
        about = QAction("&About PreflightQC", self)
        about.triggered.connect(self._on_about)
        help_menu.addAction(about)

    # -- input --------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 - Qt override
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 - Qt override
        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
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
        self._findings_view.clear()
        self._metadata_view.clear()
        self._set_export_enabled(False)
        self._set_status_message("Cleared.")

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
        self._set_status_message(f"{option.display_name} — {option.subtitle}")

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
        self._progress.setRange(0, len(self._paths))
        self._progress.setValue(0)
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

    @Slot(object)
    def _on_progress(self, progress: BatchProgress) -> None:
        self._progress.setValue(progress.completed)
        self._progress.setFormat(f"{progress.completed} of {progress.total}")

    @Slot(object)
    def _on_batch_finished(self, outcome) -> None:
        self._outcome = outcome
        self._set_running(False)
        pairs = viewmodels.build_summary_pairs(outcome.summary)
        self._summary_label.setText("   ".join(f"{name}: {count}" for name, count in pairs))
        self._set_export_enabled(True)
        if outcome.cancelled:
            self._set_status_message("Cancelled. Partial results are shown and can be exported.")
        else:
            self._set_status_message("Check complete.")

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
        for index in range(len(self._paths)):
            self._update_row(index)

    def _update_row(self, index: int) -> None:
        row = viewmodels.build_file_row(index, self._paths[index], self._results.get(index))
        style = severity_style.for_status(row.status) if row.status else None

        status_item = QTableWidgetItem(style.label if style else "…")
        if style is not None:
            status_item.setText(f"{style.marker} {style.label}")
        name_item = QTableWidgetItem(row.name)
        name_item.setToolTip(row.path)
        result_item = QTableWidgetItem(row.summary_text)
        if row.failure_hint:
            result_item.setToolTip(row.failure_hint)

        for column, item in enumerate((status_item, name_item, result_item)):
            self._table.setItem(index, column, item)
        self._table.resizeColumnToContents(0)

    @Slot()
    def _on_selection_changed(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        result = self._results.get(rows[0].row())
        if result is None:
            self._findings_view.setPlainText("This file has not been checked yet.")
            self._metadata_view.clear()
            return
        detail = viewmodels.build_file_detail(result)
        self._findings_view.setHtml(_render_findings(detail))
        self._metadata_view.setHtml(_render_metadata(detail))

    def _set_status_message(self, message: str) -> None:
        self.statusBar().showMessage(message)

    # -- export -------------------------------------------------------------

    @Slot()
    def _on_export(self, fmt: ExportFormat) -> None:
        preset = self._selected_preset()
        if self._outcome is None or preset is None or self._started_at is None:
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
            self._set_status_message(
                "Exported " + ", ".join(p.name for p in result.written)
            )
        else:
            QMessageBox.warning(self, "Export failed", f"{result.error}\n\n{result.hint}")

    # -- dialogs ------------------------------------------------------------

    @Slot()
    def _on_about(self) -> None:
        AboutDialog(self._startup, parent=self).exec()

    def _show_startup_problem(self) -> None:
        QMessageBox.critical(
            self,
            "Inspectors unavailable",
            "PreflightQC could not start its bundled inspection tools.\n\n"
            + "\n\n".join(self._startup.problems()),
        )

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        """Cancel and reap before exiting, so no inspector process is orphaned."""
        if self._token is not None:
            self._token.cancel()
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(5000)
        event.accept()


def _render_findings(detail: viewmodels.FileDetail) -> str:
    if not detail.findings:
        return (
            f"<p><b>{detail.status}</b></p>"
            f"<p>All {detail.checks_passed} checks in this preset passed.</p>"
        )
    parts = [f"<p><b>{detail.status}</b> — {detail.checks_passed} checks passed</p>"]
    for finding in detail.findings:
        style = severity_style.for_severity(finding.severity)
        parts.append(
            f"<div style='margin:10px 0;padding:8px;border-left:4px solid {style.background}'>"
            f"<div><span style='{severity_style.badge_stylesheet(style)}'>"
            f"{style.marker} {style.label}</span> <b>{finding.property_label}</b></div>"
            f"<div style='margin-top:4px'>Detected: <code>{finding.detected}</code></div>"
            f"<div>Expected: <code>{finding.expected}</code></div>"
            f"<div style='margin-top:4px'>{finding.explanation}</div>"
            + (
                f"<div style='color:#5c666e'>Not evaluated: {finding.unknown_reason}</div>"
                if finding.unknown_reason
                else ""
            )
            + (
                f"<div style='color:#5c666e;font-size:11px'>Read from {finding.provenance}</div>"
                if finding.provenance
                else ""
            )
            + f"<div style='color:#5c666e;font-size:11px'>{finding.source_line}</div>"
            f"<div style='color:#5c666e;font-size:11px'>Rule: {finding.rule_id}</div>"
            "</div>"
        )
    return "".join(parts)


def _render_metadata(detail: viewmodels.FileDetail) -> str:
    rows = [
        "<tr><th align='left'>Property</th><th align='left'>Value</th>"
        "<th align='left'>State</th><th align='left'>Source</th></tr>"
    ]
    for row in detail.metadata:
        muted = "" if row.state == "KNOWN" else " style='color:#5c666e'"
        rows.append(
            f"<tr{muted}><td>{row.label}</td><td>{row.value}</td>"
            f"<td>{row.state}</td><td style='font-size:11px'>{row.provenance}</td></tr>"
        )
    diagnostics = "".join(f"<p style='color:#5c666e'>{note}</p>" for note in detail.diagnostics)
    return f"<table cellpadding='4'>{''.join(rows)}</table>{diagnostics}"
