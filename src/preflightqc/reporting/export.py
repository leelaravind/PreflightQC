"""Report export.

Two properties matter more than the file format (spec 23):

* **Results are never lost.** Rendering happens fully in memory before anything is
  written, and the write is atomic. A full disk or a read-only destination produces an
  actionable error with the results still available to retry elsewhere.
* **The default destination is never the source video folder.** Writing a report beside
  a client's masters is presumptuous at best, and on a read-only delivery drive it just
  fails.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from preflightqc.platform.paths import atomic_write_bytes, atomic_write_text, user_data_dir
from preflightqc.reporting import csv_writer, html_renderer
from preflightqc.reporting.model import ReportModel


class ExportFormat(Enum):
    CSV = "csv"
    HTML = "html"


@dataclass(frozen=True, slots=True)
class ExportResult:
    ok: bool
    written: tuple[Path, ...] = ()
    error: str = ""
    hint: str = ""


def default_output_dir() -> Path:
    """A user-writable default that is never the folder holding the source videos."""
    return user_data_dir() / "reports"


def suggested_filename(report: ReportModel, fmt: ExportFormat) -> str:
    stamp = report.scan_started.replace(":", "-").replace("T", "_")
    return f"preflightqc_{report.preset_id}_{stamp}.{fmt.value}"


def export(report: ReportModel, destination: Path, fmt: ExportFormat) -> ExportResult:
    """Render and write a report. Never raises; returns a structured outcome."""
    try:
        if fmt is ExportFormat.HTML:
            payload = html_renderer.render(report)
        else:
            payload = csv_writer.render_findings(report)
            summary = csv_writer.render_summary(report)
    except Exception as exc:
        return ExportResult(
            ok=False,
            error=f"the report could not be generated: {type(exc).__name__}: {exc}",
            hint="Your results are still loaded. This is a defect in PreflightQC.",
        )

    written: list[Path] = []
    try:
        if fmt is ExportFormat.HTML:
            atomic_write_text(destination, payload)
            written.append(destination)
        else:
            atomic_write_bytes(destination, csv_writer.encode(payload))
            written.append(destination)
            summary_path = destination.with_name(f"{destination.stem}_summary.csv")
            atomic_write_bytes(summary_path, csv_writer.encode(summary))
            written.append(summary_path)
    except OSError as exc:
        return ExportResult(
            ok=False,
            error=f"could not write to {destination}: {exc}",
            hint=(
                "Choose a different folder, or check that the drive has free space and "
                "is not read-only. Your results are still loaded and can be exported again."
            ),
        )

    return ExportResult(ok=True, written=tuple(written))
