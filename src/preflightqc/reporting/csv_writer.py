"""CSV export.

UTF-8 **with a BOM**, because the primary consumer is Excel on Windows and Excel
misreads a BOM-less UTF-8 CSV as the system codepage -- which mangles every non-ASCII
filename in a delivery report.

RFC 4180 quoting and CRLF line endings for the same reason. Column order is fixed so
that a saved template or a downstream script does not break between versions.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from preflightqc.reporting.model import ReportModel

FINDING_COLUMNS: tuple[str, ...] = (
    "file_name",
    "file_path",
    "file_status",
    "severity",
    "classification",
    "rule_id",
    "property",
    "detected_value",
    "expected_value",
    "explanation",
    "unknown_reason",
    "source_title",
    "source_url",
    "source_access_date",
    "source_confidence",
    "detected_by",
    "check_passed",
)

SUMMARY_COLUMNS: tuple[str, ...] = ("metric", "value")


def _writer(buffer: io.StringIO) -> Any:
    """csv.writer has no public type to annotate against."""
    return csv.writer(buffer, dialect="excel", lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)


def render_findings(report: ReportModel, *, include_passed: bool = False) -> str:
    """One row per finding. Passing checks are excluded unless asked for."""
    buffer = io.StringIO()
    writer = _writer(buffer)
    writer.writerow(FINDING_COLUMNS)

    for file in report.files:
        findings = file.findings if include_passed else file.actionable
        if not findings:
            # Every file gets at least one row. A file that silently disappears from the
            # findings export is one the reader assumes was never checked -- which is
            # exactly wrong for a clean file, and dangerous for one that failed to open.
            explanation = (
                file.failure_message
                if file.failure_message
                else f"All {file.checks_passed} checks in this preset passed."
            )
            writer.writerow(
                [
                    file.name,
                    file.path,
                    file.status,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    explanation,
                    file.failure_hint,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
            continue
        for finding in findings:
            writer.writerow(
                [
                    file.name,
                    file.path,
                    file.status,
                    finding.severity,
                    finding.classification,
                    finding.rule_id,
                    finding.property_label,
                    finding.detected,
                    finding.expected,
                    finding.explanation,
                    finding.unknown_reason,
                    finding.source_title,
                    finding.source_url,
                    finding.source_access_date,
                    finding.source_confidence,
                    finding.provenance,
                    "yes" if finding.passed else "no",
                ]
            )
    return buffer.getvalue()


def render_summary(report: ReportModel) -> str:
    """The batch totals and the provenance a reader needs to trust them."""
    buffer = io.StringIO()
    writer = _writer(buffer)
    writer.writerow(SUMMARY_COLUMNS)

    rows: list[tuple[str, str]] = [
        ("PreflightQC version", report.product_version),
        ("Scan started", report.scan_started),
        ("Scan finished", report.scan_finished),
        ("Timezone", report.timezone),
        ("Preset", report.preset_display_name),
        ("Preset id", report.preset_id),
        ("Platform", report.preset_platform),
        ("Rule-set version", report.ruleset_version),
        ("Rules last verified", report.preset_last_verified),
        ("Files added", str(report.total_files)),
        ("Files inspected", str(report.inspected)),
    ]
    rows.extend((f"Files {status}", str(count)) for status, count in report.status_counts.items())
    rows.extend(
        (f"Findings {severity}", str(count)) for severity, count in report.severity_counts.items()
    )
    rows.extend(
        (f"Inspector {name}", version) for name, version in sorted(report.inspector_versions.items())
    )
    rows.append(("Report complete", "no (partial)" if report.is_partial else "yes"))
    if report.partial_note:
        rows.append(("Partial reason", report.partial_note))
    if report.byte_convention:
        rows.append(("Byte convention", report.byte_convention))
    rows.append(("Validation basis", report.approved_claim))
    rows.append(("Source files", report.non_destructive_statement))
    rows.append(("Accuracy", report.accuracy_statement))
    rows.extend(("Preset caveat", caveat) for caveat in report.preset_caveats)
    rows.extend(("Not processed", path) for path in report.unprocessed)

    writer.writerows(rows)
    return buffer.getvalue()


def encode(text: str) -> bytes:
    """UTF-8 with a BOM, for Excel."""
    return text.encode("utf-8-sig")
