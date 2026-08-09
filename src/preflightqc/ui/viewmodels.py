"""Immutable view-model snapshots.

The UI never reads mutable domain state across a thread boundary. The orchestrator
publishes a snapshot; the UI renders it. That is what keeps a 1000-file batch from
tearing the table while the user is reading it, and it removes every lock from the
rendering path.

These types are Qt-free so they can be built and asserted on in a headless test.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from preflightqc.results.aggregate import BatchSummary, FileResult, FileStatus
from preflightqc.rules.document import PresetDocument
from preflightqc.rules.severity import Severity


@dataclass(frozen=True, slots=True)
class FindingRow:
    rule_id: str
    severity: str
    property_label: str
    detected: str
    expected: str
    explanation: str
    source_line: str
    provenance: str
    unknown_reason: str


@dataclass(frozen=True, slots=True)
class FileRow:
    """One row of the batch table."""

    index: int
    name: str
    path: str
    status: str
    fail_count: int
    warn_count: int
    unknown_count: int
    checks_passed: int
    failure_message: str
    failure_hint: str
    is_complete: bool

    @property
    def summary_text(self) -> str:
        if not self.is_complete:
            return "queued"
        if self.failure_message:
            return self.failure_message
        parts = []
        if self.fail_count:
            parts.append(f"{self.fail_count} fail")
        if self.warn_count:
            parts.append(f"{self.warn_count} warning")
        if self.unknown_count:
            parts.append(f"{self.unknown_count} unknown")
        return ", ".join(parts) if parts else f"{self.checks_passed} checks passed"


@dataclass(frozen=True, slots=True)
class MetadataRow:
    """One row of the metadata inspector.

    `state` is rendered explicitly so a user can tell "not present in this file" from
    "we could not determine it" -- a distinction the whole severity model rests on.
    """

    label: str
    value: str
    state: str
    provenance: str


@dataclass(frozen=True, slots=True)
class FileDetail:
    name: str
    path: str
    status: str
    findings: tuple[FindingRow, ...]
    metadata: tuple[MetadataRow, ...]
    diagnostics: tuple[str, ...]
    checks_passed: int


@dataclass(frozen=True, slots=True)
class PresetOption:
    preset_id: str
    display_name: str
    platform: str
    ruleset_version: str
    last_verified: str
    caveats: tuple[str, ...]
    is_custom: bool

    @property
    def subtitle(self) -> str:
        return f"rules {self.ruleset_version} · verified {self.last_verified}"


@dataclass(frozen=True, slots=True)
class BatchViewModel:
    rows: tuple[FileRow, ...]
    total: int
    completed: int
    in_flight: int
    running: bool
    cancelled: bool
    summary: tuple[tuple[str, int], ...] = field(default_factory=tuple)

    @property
    def progress_text(self) -> str:
        if not self.running and self.completed == 0:
            return f"{self.total} file(s) ready"
        return f"{self.completed} of {self.total} complete"


def build_preset_options(presets: Sequence[PresetDocument]) -> tuple[PresetOption, ...]:
    return tuple(
        PresetOption(
            preset_id=p.preset_id,
            display_name=p.display_name,
            platform="Custom profile" if p.is_custom else p.platform,
            ruleset_version=p.ruleset_version,
            last_verified=p.last_verified_date,
            caveats=p.caveats,
            is_custom=p.is_custom,
        )
        for p in presets
    )


def build_file_row(index: int, path: Path, result: FileResult | None) -> FileRow:
    if result is None:
        return FileRow(
            index=index,
            name=path.name,
            path=str(path),
            status="",
            fail_count=0,
            warn_count=0,
            unknown_count=0,
            checks_passed=0,
            failure_message="",
            failure_hint="",
            is_complete=False,
        )
    counts = result.counts
    return FileRow(
        index=index,
        name=result.display_name,
        path=str(result.path),
        status=result.status.value,
        fail_count=counts.get(Severity.FAIL, 0),
        warn_count=counts.get(Severity.WARN, 0),
        unknown_count=counts.get(Severity.UNKNOWN, 0),
        checks_passed=result.checks_passed,
        failure_message=result.failure.message if result.failure else "",
        failure_hint=(result.failure.hint or "") if result.failure else "",
        is_complete=True,
    )


def build_summary_pairs(summary: BatchSummary) -> tuple[tuple[str, int], ...]:
    """The five counters, always all five, so NOT_INSPECTED is never hidden."""
    return tuple(
        (status.value.replace("_", " ").title(), summary.status_counts.get(status, 0))
        for status in FileStatus
    )


def _metadata_rows(result: FileResult) -> tuple[MetadataRow, ...]:
    from preflightqc.core.model import PROPERTY_PATHS

    if result.media is None:
        return ()
    rows: list[MetadataRow] = []
    for descriptor in PROPERTY_PATHS.values():
        field = descriptor.resolve(result.media)
        provenance = field.provenance.describe() if field.provenance else ""
        rows.append(
            MetadataRow(
                label=descriptor.label + (f" ({descriptor.unit})" if descriptor.unit else ""),
                value=field.describe(),
                state=field.state.value,
                provenance=provenance,
            )
        )
    return tuple(rows)


def build_file_detail(result: FileResult) -> FileDetail:
    findings = tuple(
        FindingRow(
            rule_id=f.rule_id,
            severity=f.severity.value,
            property_label=f.property_label,
            detected=f.detected,
            expected=f.expected,
            explanation=f.explanation,
            source_line=(
                f"{f.source.title} — {f.source.url} "
                f"(accessed {f.source.access_date}, confidence {f.source.confidence})"
            ),
            provenance=f.provenance or "",
            unknown_reason=f.unknown_reason or "",
        )
        for f in result.actionable_findings
    )
    return FileDetail(
        name=result.display_name,
        path=str(result.path),
        status=result.status.value,
        findings=findings,
        metadata=_metadata_rows(result),
        diagnostics=tuple(result.diagnostics.notes),
        checks_passed=result.checks_passed,
    )
