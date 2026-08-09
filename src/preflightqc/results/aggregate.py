"""Per-file and per-batch result aggregation.

Specification 7.2 in executable form:

    if any FAIL   -> FAIL
    elif any WARN -> WARN
    else          -> PASS

INFO and UNKNOWN are **structurally excluded** from the computation. `overall_status`
does not receive them at all -- they are filtered before the function is called, rather
than being skipped by a condition inside it that a later edit could weaken. "We could
not determine this" must never read as "your file is wrong".
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from preflightqc.core.model import Diagnostics, NormalisedMedia
from preflightqc.rules.finding import Finding
from preflightqc.rules.severity import Severity


class FileStatus(Enum):
    """The overall verdict for one file. Spec 7.2 and 7.4."""

    PASS = "PASS"  # noqa: S105 - a file status, not a credential
    WARN = "WARN"
    FAIL = "FAIL"

    NOT_INSPECTED = "NOT_INSPECTED"
    """The file could not be inspected at all. This is **not** a FAIL: the file was
    never validated, so PreflightQC has no opinion on its conformance."""

    NOT_APPLICABLE = "NOT_APPLICABLE"
    """The file is not something the selected preset can be applied to."""

    @property
    def is_verdict(self) -> bool:
        """True for the three statuses that represent an actual validation result."""
        return self in (FileStatus.PASS, FileStatus.WARN, FileStatus.FAIL)


#: The severities that participate in the overall-status decision. Deliberately a
#: module-level constant so the exclusion of INFO and UNKNOWN is visible and testable.
DECIDING_SEVERITIES = (Severity.FAIL, Severity.WARN)


def overall_status(deciding: tuple[Severity, ...]) -> FileStatus:
    """Compute the overall status from the deciding severities only.

    The caller must pass only FAIL and WARN severities; anything else is a programming
    error and raises, rather than being silently ignored.
    """
    for severity in deciding:
        if severity not in DECIDING_SEVERITIES:
            raise ValueError(
                f"{severity.value} must not participate in overall status (spec 7.2)"
            )
    if Severity.FAIL in deciding:
        return FileStatus.FAIL
    if Severity.WARN in deciding:
        return FileStatus.WARN
    return FileStatus.PASS


def deciding_severities(findings: tuple[Finding, ...]) -> tuple[Severity, ...]:
    """Extract only the severities that may decide the overall status.

    Passing findings are excluded: a satisfied rule is evidence of conformance, not of
    failure.
    """
    return tuple(
        finding.severity
        for finding in findings
        if not finding.passed and finding.severity in DECIDING_SEVERITIES
    )


@dataclass(frozen=True, slots=True)
class InspectionFailure:
    """Why a file could not be inspected. Spec 23."""

    kind: str
    message: str
    hint: str | None = None

    def describe(self) -> str:
        return f"{self.message} ({self.kind})" + (f" — {self.hint}" if self.hint else "")


@dataclass(frozen=True, slots=True)
class FileResult:
    """The complete outcome for one file. Spec 14.1."""

    path: Path
    display_name: str
    status: FileStatus
    findings: tuple[Finding, ...]
    preset_id: str
    ruleset_version: str
    media: NormalisedMedia | None = None
    failure: InspectionFailure | None = None
    diagnostics: Diagnostics = field(default_factory=Diagnostics)
    duration_ms: float = 0.0

    @property
    def counts(self) -> dict[Severity, int]:
        """Counts by severity over findings that represent an actual observation.

        Passing findings are excluded so that "3 WARN" means three warnings, not three
        warnings plus forty satisfied checks.
        """
        counter: Counter[Severity] = Counter(
            finding.severity for finding in self.findings if not finding.passed
        )
        return {severity: counter.get(severity, 0) for severity in Severity}

    @property
    def checks_passed(self) -> int:
        return sum(1 for finding in self.findings if finding.passed)

    @property
    def actionable_findings(self) -> tuple[Finding, ...]:
        return tuple(finding for finding in self.findings if not finding.passed)

    @property
    def was_inspected(self) -> bool:
        return self.status.is_verdict


def build_file_result(
    *,
    path: Path,
    media: NormalisedMedia,
    findings: tuple[Finding, ...],
    preset_id: str,
    ruleset_version: str,
    duration_ms: float = 0.0,
) -> FileResult:
    """Build the result for a file that was successfully inspected and validated."""
    return FileResult(
        path=path,
        display_name=path.name,
        status=overall_status(deciding_severities(findings)),
        findings=findings,
        preset_id=preset_id,
        ruleset_version=ruleset_version,
        media=media,
        diagnostics=media.diagnostics,
        duration_ms=duration_ms,
    )


def build_not_inspected(
    *,
    path: Path,
    failure: InspectionFailure,
    preset_id: str,
    ruleset_version: str,
    diagnostics: Diagnostics | None = None,
    duration_ms: float = 0.0,
) -> FileResult:
    """Build the result for a file that could not be inspected.

    Note the status: NOT_INSPECTED, never FAIL. PreflightQC did not validate this file,
    so it must not imply a verdict about it.
    """
    return FileResult(
        path=path,
        display_name=path.name,
        status=FileStatus.NOT_INSPECTED,
        findings=(),
        preset_id=preset_id,
        ruleset_version=ruleset_version,
        media=None,
        failure=failure,
        diagnostics=diagnostics or Diagnostics(),
        duration_ms=duration_ms,
    )


@dataclass(frozen=True, slots=True)
class BatchSummary:
    """Batch totals. Derived, never stored alongside as a second source of truth."""

    total_files: int
    inspected: int
    status_counts: dict[FileStatus, int]
    severity_counts: dict[Severity, int]
    preset_id: str
    preset_display_name: str
    ruleset_version: str
    completed: bool
    cancelled: bool

    @property
    def passed(self) -> int:
        return self.status_counts.get(FileStatus.PASS, 0)

    @property
    def warned(self) -> int:
        return self.status_counts.get(FileStatus.WARN, 0)

    @property
    def failed(self) -> int:
        return self.status_counts.get(FileStatus.FAIL, 0)

    @property
    def not_inspected(self) -> int:
        return self.status_counts.get(FileStatus.NOT_INSPECTED, 0)

    @property
    def not_applicable(self) -> int:
        return self.status_counts.get(FileStatus.NOT_APPLICABLE, 0)

    @property
    def is_partial(self) -> bool:
        return self.cancelled or not self.completed


def summarise(
    results: tuple[FileResult, ...],
    *,
    preset_id: str,
    preset_display_name: str,
    ruleset_version: str,
    total_files: int | None = None,
    completed: bool = True,
    cancelled: bool = False,
) -> BatchSummary:
    """Derive the batch summary.

    NOT_INSPECTED and NOT_APPLICABLE get their own counters and are never folded into
    the FAIL count (spec 14.2).
    """
    status_counter: Counter[FileStatus] = Counter(result.status for result in results)
    severity_counter: Counter[Severity] = Counter()
    for result in results:
        for severity, count in result.counts.items():
            severity_counter[severity] += count

    return BatchSummary(
        total_files=total_files if total_files is not None else len(results),
        inspected=sum(1 for result in results if result.was_inspected),
        status_counts={status: status_counter.get(status, 0) for status in FileStatus},
        severity_counts={severity: severity_counter.get(severity, 0) for severity in Severity},
        preset_id=preset_id,
        preset_display_name=preset_display_name,
        ruleset_version=ruleset_version,
        completed=completed,
        cancelled=cancelled,
    )
