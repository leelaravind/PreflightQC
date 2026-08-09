"""Render the application's principal states to PNG for human review (plan §20/§21).

These are **real renders of the real widgets**, not mock-ups. The window is constructed
exactly as the product constructs it, driven with results from a real batch over real
media using the real bundled inspectors, and captured with ``QWidget.grab()``. Nothing
here is drawn by hand, and if a state cannot be produced it is skipped with a reason
rather than faked.

    python tools/capture_screens.py --out docs/design/screens/after
    python tools/capture_screens.py --scale 1.5      # simulate 150% display scaling

The scale option exists because DPI scaling is where Qt layouts break, and "it looked
fine on my monitor" is not a test.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

SAMPLES = REPO_ROOT / "spikes" / "samples"

#: A small, deliberately mixed batch: a conformant file, a file with no audio, a portrait
#: file judged against a landscape preset, and a destroyed one. Between them they produce
#: PASS, WARN, FAIL and an inspector error in a single screenshot.
BATCH: tuple[str, ...] = (
    "01_h264_1080x1920_30_aac.mp4",
    "03_h264_1920x1080_25.mp4",
    "02_h264_no_audio.mp4",
    "04_anamorphic_sar43.mp4",
    "94_corrupt_moov.mp4",
    "92_not_media.mp4",
)

PRESET_ID = "ig_reels"


@dataclass
class Shot:
    name: str
    title: str
    captured: bool
    detail: str = ""


def _configure_scaling(scale: float) -> None:
    if scale != 1.0:
        # Qt reads these before the QApplication exists; setting them later does nothing.
        os.environ["QT_SCALE_FACTOR"] = str(scale)
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture application states for review")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "docs" / "design" / "screens")
    parser.add_argument("--scale", type=float, default=1.0)
    args = parser.parse_args()

    _configure_scaling(args.scale)

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from preflightqc.orchestration.runner import BatchRunner, CancellationToken, InspectionSettings
    from preflightqc.platform import binaries
    from preflightqc.ui.about import AboutDialog
    from preflightqc.ui.main_window import MainWindow

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    shots: list[Shot] = []

    from preflightqc.ui.theme import apply_theme

    app = QApplication.instance() or QApplication([])
    apply_theme(app)

    def capture(widget, name: str, title: str) -> None:
        widget.show()
        app.processEvents()
        QTimer.singleShot(0, lambda: None)
        app.processEvents()
        pixmap = widget.grab()
        path = out / f"{name}.png"
        ok = pixmap.save(str(path))
        shots.append(Shot(name, title, ok, f"{pixmap.width()}x{pixmap.height()}"))
        print(f"  {'OK ' if ok else 'FAIL'} {name:26} {pixmap.width()}x{pixmap.height()}  {title}")

    window = MainWindow()
    window.resize(1180, 780)

    # 1 — first launch, nothing loaded.
    capture(window, "01-empty-state", "First launch / empty state")

    paths = [SAMPLES / name for name in BATCH if (SAMPLES / name).is_file()]
    if not paths:
        print(f"\nNo sample media in {SAMPLES}; only the empty state could be captured.")
        _write_index(out, shots, args.scale)
        return 0

    # 2 — files loaded, before any check has run.
    window._add_paths(paths)

    # A file that vanished between being queued and being checked is a real scenario --
    # a render farm cleaning up, a network share dropping -- and it is the only way to
    # produce NOT_INSPECTED. Appended directly because enumeration would filter it out.
    missing = SAMPLES / "99_removed_before_check.mp4"
    window._paths.append(missing)
    paths = list(window._paths)
    window._refresh_table()
    capture(window, "02-files-loaded", "Files loaded, not yet checked")

    # 3 — preset selected. Selecting it publishes the ruleset version to the status bar.
    index = window._preset_box.findData(PRESET_ID)
    if index >= 0:
        window._preset_box.setCurrentIndex(index)
    capture(window, "03-preset-selected", "Preset selected")

    preset = window._selected_preset()
    startup = binaries.check_all()
    runner = BatchRunner(startup=startup, settings=InspectionSettings())

    # 4 — mid-scan. Captured by rendering after a partial run rather than by racing a
    # real batch, so the frame is deterministic.
    partial = runner.run(paths[:2], preset, token=CancellationToken())
    for position, result in enumerate(partial.results):
        window._results[position] = result
        window._update_row(position)
    window._set_running(True)
    window._progress.setRange(0, len(paths))
    window._progress.setValue(2)
    window._progress.setFormat(f"2 of {len(paths)}")
    capture(window, "04-scanning", "Check in progress")

    # 5 — the full batch.
    window._started_at = datetime.now().astimezone()
    outcome = runner.run(paths, preset, token=CancellationToken())
    window._results.clear()
    for position, result in enumerate(outcome.results):
        window._results[position] = result
    window._refresh_table()
    window._on_batch_finished(outcome)
    capture(window, "05-mixed-batch", "Mixed batch, complete")

    # 6-9 — one screenshot per outcome class, selecting the first row that produced it.
    wanted = {
        "PASS": ("06-pass-detail", "PASS result with findings detail"),
        "WARN": ("07-warn-detail", "WARN result with findings detail"),
        "FAIL": ("08-fail-detail", "FAIL result with findings detail"),
        "NOT_INSPECTED": ("10-error-state", "Inspector error / unreadable file"),
    }
    seen: set[str] = set()
    for position, result in enumerate(outcome.results):
        status = result.status.value
        if status in wanted and status not in seen:
            seen.add(status)
            name, title = wanted[status]
            window._table.selectRow(position)
            app.processEvents()
            capture(window, name, title)

    for status, (name, title) in wanted.items():
        if status not in seen:
            shots.append(Shot(name, title, False, f"no file in the sample batch produced {status}"))
            print(f"  --  {name:26} skipped: no {status} in this batch")

    # 9 — the metadata tab, which is where the undetermined-vs-absent distinction shows.
    window._detail_tabs.setCurrentIndex(1)
    app.processEvents()
    capture(window, "09-metadata-tab", "Metadata inspector (KNOWN / UNDETERMINED states)")
    window._detail_tabs.setCurrentIndex(0)

    # 11 — the preset selector expanded, showing shipped presets and any custom profile.
    window._preset_box.showPopup()
    app.processEvents()
    view = window._preset_box.view()
    if view is not None and view.isVisible():
        capture(view.window(), "11-preset-list", "Preset and custom-profile selector")
    else:
        shots.append(Shot("11-preset-list", "Preset selector", False, "popup did not render offscreen"))
    window._preset_box.hidePopup()

    # 12 — the export deliverable. Not a screenshot: the real HTML report, written where
    # a reviewer can open it. Rendering someone else's HTML inside a QTextBrowser would
    # show a picture of the wrong thing.
    exported = _export_report(window, outcome, preset, out)
    shots.append(
        Shot(
            "12-export",
            "Exported HTML report (open in a browser)",
            exported is not None,
            exported.name if exported else "export failed",
        )
    )
    print(f"  {'OK ' if exported else 'FAIL'} 12-export{' ' * 18} {exported.name if exported else ''}")

    # 13 — About, including the third-party notices tab.
    about = AboutDialog(startup, parent=window)
    about.resize(760, 560)
    capture(about, "13-about", "About / legal information")
    tabs = about.findChildren(type(about.layout().itemAt(0).widget()))
    if tabs:
        tabs[0].setCurrentIndex(1)
        app.processEvents()
        capture(about, "13b-about-notices", "About — third-party notices")
    about.close()

    window.close()
    _write_index(out, shots, args.scale)
    captured = sum(1 for shot in shots if shot.captured)
    print(f"\n{captured}/{len(shots)} states captured into {out}")
    return 0


def _export_report(window, outcome, preset, out: Path) -> Path | None:
    """Write the real HTML report the product exports, for the reviewer to open."""
    from datetime import datetime as _dt

    from preflightqc import __version__
    from preflightqc.reporting import export as export_module
    from preflightqc.reporting.export import ExportFormat
    from preflightqc.reporting.model import build_report

    report = build_report(
        results=outcome.results,
        summary=outcome.summary,
        preset=preset,
        product_version=__version__,
        scan_started=window._started_at,
        scan_finished=_dt.now().astimezone(),
        inspector_versions=window._startup.versions(),
    )
    destination = out / "12-export-report.html"
    result = export_module.export(report, destination, ExportFormat.HTML)
    return destination if result.ok else None


def _write_index(out: Path, shots: list[Shot], scale: float) -> None:
    lines = [
        "# PreflightQC — captured application states",
        "",
        f"Rendered at {scale:g}x display scaling by `tools/capture_screens.py`.",
        "Real widgets, real media, real bundled inspectors. Nothing is a mock-up.",
        "",
        "| State | File | Captured |",
        "| --- | --- | --- |",
    ]
    for shot in shots:
        status = f"yes ({shot.detail})" if shot.captured else f"**no** — {shot.detail}"
        target = f"`{shot.name}.png`" if shot.captured else "—"
        lines.append(f"| {shot.title} | {target} | {status} |")
    lines.append("")
    (out / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
