"""The report model.

Built once from a batch outcome and consumed by both writers, so CSV and HTML **cannot
disagree** about a count or a status. It is also the snapshot-test target, which means a
report regression shows up as a diff on this structure rather than as a subtle
difference between two independently assembled documents.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from preflightqc.reporting import claims
from preflightqc.results.aggregate import BatchSummary, FileResult, FileStatus
from preflightqc.rules.document import PresetDocument
from preflightqc.rules.finding import Finding
from preflightqc.rules.severity import Severity


@dataclass(frozen=True, slots=True)
class ReportFinding:
    """One finding, flattened for presentation."""

    rule_id: str
    severity: str
    classification: str
    property_label: str
    property_path: str
    detected: str
    expected: str
    explanation: str
    source_title: str
    source_url: str
    source_access_date: str
    source_confidence: str
    provenance: str
    unknown_reason: str
    passed: bool


@dataclass(frozen=True, slots=True)
class ReportFile:
    """One file's section of the report."""

    name: str
    path: str
    status: str
    counts: Mapping[str, int]
    checks_passed: int
    findings: tuple[ReportFinding, ...]
    failure_kind: str
    failure_message: str
    failure_hint: str
    diagnostics: tuple[str, ...]

    @property
    def actionable(self) -> tuple[ReportFinding, ...]:
        return tuple(f for f in self.findings if not f.passed)


@dataclass(frozen=True, slots=True)
class ReportModel:
    """Everything both writers need. Spec 17.2."""

    product_version: str
    scan_started: str
    scan_finished: str
    timezone: str
    preset_id: str
    preset_display_name: str
    preset_platform: str
    ruleset_version: str
    preset_last_verified: str
    preset_caveats: tuple[str, ...]
    byte_convention: str
    inspector_versions: Mapping[str, str]
    files: tuple[ReportFile, ...]
    status_counts: Mapping[str, int]
    severity_counts: Mapping[str, int]
    total_files: int
    inspected: int
    is_partial: bool
    was_cancelled: bool
    approved_claim: str = claims.APPROVED_CLAIM
    non_destructive_statement: str = claims.NON_DESTRUCTIVE_STATEMENT
    accuracy_statement: str = claims.ACCURACY_STATEMENT
    unprocessed: tuple[str, ...] = field(default_factory=tuple)

    @property
    def partial_note(self) -> str:
        if not self.is_partial:
            return ""
        reason = "cancelled by the user" if self.was_cancelled else "did not complete"
        return (
            f"This report is PARTIAL: the batch was {reason}. "
            f"{self.inspected} of {self.total_files} files were inspected."
        )


def _flatten_finding(finding: Finding) -> ReportFinding:
    return ReportFinding(
        rule_id=finding.rule_id,
        severity=finding.severity.value,
        classification=finding.classification.value,
        property_label=finding.property_label,
        property_path=finding.property_path,
        detected=finding.detected,
        expected=finding.expected,
        explanation=finding.explanation,
        source_title=finding.source.title,
        source_url=finding.source.url,
        source_access_date=finding.source.access_date,
        source_confidence=finding.source.confidence,
        provenance=finding.provenance or "",
        unknown_reason=finding.unknown_reason or "",
        passed=finding.passed,
    )


def _flatten_file(result: FileResult) -> ReportFile:
    return ReportFile(
        name=result.display_name,
        path=str(result.path),
        status=result.status.value,
        counts={severity.value: count for severity, count in result.counts.items()},
        checks_passed=result.checks_passed,
        findings=tuple(_flatten_finding(f) for f in result.findings),
        failure_kind=result.failure.kind if result.failure else "",
        failure_message=result.failure.message if result.failure else "",
        failure_hint=(result.failure.hint or "") if result.failure else "",
        diagnostics=tuple(result.diagnostics.notes),
    )


def build_report(
    *,
    results: Sequence[FileResult],
    summary: BatchSummary,
    preset: PresetDocument,
    product_version: str,
    scan_started: datetime,
    scan_finished: datetime,
    inspector_versions: Mapping[str, str],
    unprocessed: Sequence[Path] = (),
) -> ReportModel:
    """Assemble the report model from a completed (or partial) batch."""
    return ReportModel(
        product_version=product_version,
        scan_started=scan_started.isoformat(timespec="seconds"),
        scan_finished=scan_finished.isoformat(timespec="seconds"),
        timezone=str(scan_started.tzinfo) if scan_started.tzinfo else "local time",
        preset_id=preset.preset_id,
        # A custom profile prints its own name, never a platform name (spec 16.5).
        preset_display_name=preset.display_name,
        preset_platform="Custom profile" if preset.is_custom else preset.platform,
        ruleset_version=preset.ruleset_version,
        preset_last_verified=preset.last_verified_date,
        preset_caveats=preset.caveats,
        byte_convention=preset.byte_convention or "",
        inspector_versions=dict(inspector_versions),
        files=tuple(_flatten_file(r) for r in results),
        status_counts={s.value: summary.status_counts.get(s, 0) for s in FileStatus},
        severity_counts={s.value: summary.severity_counts.get(s, 0) for s in Severity},
        total_files=summary.total_files,
        inspected=summary.inspected,
        is_partial=summary.is_partial,
        was_cancelled=summary.cancelled,
        unprocessed=tuple(str(p) for p in unprocessed),
    )
