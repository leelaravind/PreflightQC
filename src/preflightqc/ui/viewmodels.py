"""Immutable view-model snapshots.

The UI never reads mutable domain state across a thread boundary. The orchestrator
publishes a snapshot; the UI renders it. That is what keeps a 1000-file batch from
tearing the table while the user is reading it, and it removes every lock from the
rendering path.

These types are Qt-free so they can be built and asserted on in a headless test — which
is also why all presentation *logic* lives here rather than in the widgets. Value
humanising, severity ordering and the inconclusive qualifier are decisions worth testing,
and none of them needs a window to be correct.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from preflightqc.results.aggregate import BatchSummary, FileResult, FileStatus
from preflightqc.rules.document import PresetDocument
from preflightqc.rules.severity import Severity

# ---------------------------------------------------------------------------
# Value presentation
#
# The engine's strings are correct and machine-shaped: `False`, `0.5625`,
# `required: True`. A video professional reads 9:16, not 0.5625. Humanising happens
# here, in one place, on the way to the screen -- never in the engine, whose strings
# also feed exports and tests.
# ---------------------------------------------------------------------------

#: Aspect ratios that actually appear in delivery specifications, by the name a video
#: professional uses. Compared with a tolerance, because 0.5625 and 0.5625000001 are the
#: same ratio to everyone except a float.
_KNOWN_RATIOS: tuple[tuple[float, str], ...] = (
    (16 / 9, "16:9"),
    (9 / 16, "9:16"),
    (4 / 5, "4:5"),
    (5 / 4, "5:4"),
    (4 / 3, "4:3"),
    (3 / 4, "3:4"),
    (1.0, "1:1"),
    (2.0, "2:1"),
    (0.5, "1:2"),
    (3 / 2, "3:2"),
    (2 / 3, "2:3"),
    (16 / 10, "16:10"),
    (1.85, "1.85:1"),
    (2.35, "2.35:1"),
    (2.39, "2.39:1"),
    (21 / 9, "21:9"),
)

_RATIO_TOLERANCE = 0.005

_BOOLEAN_WORDS: dict[str, str] = {
    "true": "yes",
    "false": "no",
}

#: Properties whose bare boolean reads badly. "Fast start: yes" is fine; "Fast start:
#: enabled" is better, and the difference matters in a finding a user acts on.
_BOOLEAN_PHRASING: dict[str, tuple[str, str]] = {
    "container.fast_start": ("enabled", "not enabled"),
    "audio.present": ("present", "not present"),
    "video.gop_closed": ("closed", "not closed"),
    "container.edit_lists_present": ("present", "not present"),
}

_BYTE_UNITS = ("bytes", "KB", "MB", "GB", "TB")


def format_bytes(value: int) -> str:
    """`104857600` -> `104.9 MB (104,857,600 bytes)`.

    Decimal units, matching the byte convention the presets declare. Both forms are
    shown because the exact count is what a size limit is actually expressed in.
    """
    if value < 1000:
        return f"{value:,} bytes"
    size = float(value)
    unit = 0
    while size >= 1000 and unit < len(_BYTE_UNITS) - 1:
        size /= 1000
        unit += 1
    return f"{size:,.1f} {_BYTE_UNITS[unit]} ({value:,} bytes)"


def format_ratio(value: float) -> str:
    """`0.5625` -> `9:16 (0.5625)`; an unrecognised ratio keeps its decimal form.

    Deliberately a lookup and not a rational approximation. Every float is within a
    hair of *some* small fraction — 1.234567 approximates to 21:17 — and a name a user
    has never seen is worse than the number they can at least compare. The list holds
    the ratios that actually appear in delivery specifications; anything else prints as
    a decimal and says so honestly.
    """
    for target, name in _KNOWN_RATIOS:
        if abs(value - target) <= _RATIO_TOLERANCE:
            return f"{name} ({value:g})"
    return f"{value:g}"


def humanise_value(text: str, property_path: str = "") -> str:
    """Render an engine value string the way a person would say it."""
    stripped = text.strip()
    lowered = stripped.lower()

    if lowered in _BOOLEAN_WORDS:
        phrasing = _BOOLEAN_PHRASING.get(property_path)
        if phrasing is not None:
            return phrasing[0] if lowered == "true" else phrasing[1]
        return _BOOLEAN_WORDS[lowered]

    if property_path.endswith("aspect_ratio"):
        try:
            return format_ratio(float(stripped))
        except ValueError:
            pass

    if property_path == "file.size_bytes":
        try:
            return format_bytes(int(float(stripped)))
        except ValueError:
            pass

    return stripped


#: The engine phrases expectations with a leading qualifier so the classification is
#: never lost. Splitting it lets the interface show the qualifier as a label and the
#: value as a value, instead of `Expected: required: True`.
_EXPECTATION_PREFIXES: tuple[tuple[str, str], ...] = (
    ("required: ", "Required"),
    ("for eligibility: ", "For eligibility"),
    ("recommended: ", "Recommended"),
)

_CLASSIFICATION_LABELS: dict[str, str] = {
    "HARD_REQUIREMENT": "Hard requirement",
    "DOCUMENTED_LIMIT": "Documented limit",
    "RECOMMENDATION": "Recommendation",
    "BEST_PRACTICE": "Best practice",
    "ELIGIBILITY": "Eligibility",
    "UNKNOWN": "Not documented",
}


def split_expectation(text: str) -> tuple[str, str]:
    """`required: True` -> `("Required", "True")`."""
    for prefix, label in _EXPECTATION_PREFIXES:
        if text.startswith(prefix):
            return label, text[len(prefix) :]
    return "Expected", text


# ---------------------------------------------------------------------------
# Rows
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FindingRow:
    rule_id: str
    severity: str
    severity_rank: int
    classification: str
    classification_label: str
    property_label: str
    property_path: str
    detected: str
    expectation_label: str
    expected: str
    explanation: str
    source_title: str
    source_url: str
    source_access_date: str
    source_confidence: str
    provenance: str
    unknown_reason: str

    @property
    def source_line(self) -> str:
        return (
            f"{self.source_title} — {self.source_url} "
            f"(accessed {self.source_access_date}, confidence {self.source_confidence})"
        )


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
    #: True when the inspection never established that this file contains a video stream.
    #: The canonical status is unchanged; see `status_label`.
    is_inconclusive: bool = False

    #: Stated once, wherever an inconclusive result is shown.
    INCONCLUSIVE_REASON = (
        "No video stream could be read from this file, so there was nothing to check "
        "against the preset."
    )

    @property
    def display_status(self) -> str:
        """The classification the *interface* shows for this row.

        Equal to the canonical status except when the inspection established nothing, in
        which case it is `INCONCLUSIVE`. Everything on screen — the status column, the
        filter chips and the readout — uses this one value, so a single screen never
        gives two different accounts of the same batch. Exports keep `status`.
        """
        return "INCONCLUSIVE" if self.is_inconclusive else self.status

    @property
    def summary_text(self) -> str:
        if not self.is_complete:
            return "Queued"
        if self.failure_message:
            # The engine phrases failures as fragments so they read correctly inside
            # `describe()`. Standing alone in a column they need a capital.
            return self.failure_message[:1].upper() + self.failure_message[1:]
        if self.is_inconclusive:
            return f"Nothing determined — {self.unknown_count} unknown"
        parts = []
        if self.fail_count:
            parts.append(f"{self.fail_count} fail")
        if self.warn_count:
            parts.append(f"{self.warn_count} warning")
        if self.unknown_count:
            parts.append(f"{self.unknown_count} unknown")
        if not parts:
            return f"{self.checks_passed} checks passed"
        return ", ".join(parts) + f" · {self.checks_passed} passed"


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
    group: str


@dataclass(frozen=True, slots=True)
class FileDetail:
    name: str
    path: str
    status: str
    findings: tuple[FindingRow, ...]
    metadata: tuple[MetadataRow, ...]
    diagnostics: tuple[str, ...]
    checks_passed: int
    checks_total: int
    is_inconclusive: bool = False

    @property
    def status_label(self) -> str:
        return "Inconclusive" if self.is_inconclusive else self.status

    @property
    def passed_summary(self) -> str:
        return f"{self.checks_passed} of {self.checks_total} checks passed"


@dataclass(frozen=True, slots=True)
class PresetOption:
    preset_id: str
    display_name: str
    platform: str
    ruleset_version: str
    last_verified: str
    caveats: tuple[str, ...]
    is_custom: bool
    rule_count: int = 0

    @property
    def menu_label(self) -> str:
        """`Platform — Name`, without saying the platform twice.

        Nine of the twelve shipped presets name their platform in `display_name` already,
        so the naive concatenation produced "LinkedIn — LinkedIn — Connected TV (CTV)
        Ads". Fixed here rather than in the preset data, which is governed by the source
        register and must not be edited for presentation.
        """
        name = self.display_name
        prefix = f"{self.platform} — "
        if name.startswith(prefix):
            name = name[len(prefix) :]
        elif name.lower().startswith(self.platform.lower()):
            name = name[len(self.platform) :].lstrip(" \u2014\u2013-:")
        return f"{self.platform} — {name}" if name else self.platform

    @property
    def subtitle(self) -> str:
        return f"rules {self.ruleset_version} · sources verified {self.last_verified}"

    @property
    def context_line(self) -> str:
        rules = f" · {self.rule_count} rules" if self.rule_count else ""
        return f"{self.subtitle}{rules}"


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


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


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
            rule_count=len(p.rules),
        )
        for p in presets
    )


def is_inconclusive(result: FileResult) -> bool:
    """True when a *verdict* was reached without establishing that the file holds video.

    This is the whole basis of the inconclusive qualifier, and it is deliberately a
    statement about *evidence*, not about severity: if no video stream could be read,
    there was nothing for a video preset to check, so a PASS is vacuous. A zero-byte file
    and a 43-byte text file both land here; a truncated but readable file does not.

    A file that was never inspected at all — deleted between being queued and being
    checked, or unreadable — is **not** inconclusive. `NOT_INSPECTED` already says
    exactly what happened and carries its own reason; relabelling it would replace a
    precise statement with a vaguer one.
    """
    if not result.status.is_verdict:
        return False
    media = result.media
    if media is None:
        return True
    video = media.primary_video
    return video is None or not video.codec.is_known


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
        is_inconclusive=is_inconclusive(result),
    )


def build_summary_pairs(summary: BatchSummary) -> tuple[tuple[str, int], ...]:
    """The five counters, always all five, so NOT_INSPECTED is never hidden."""
    return tuple(
        (status.value.replace("_", " ").title(), summary.status_counts.get(status, 0))
        for status in FileStatus
    )


#: The order the status readout always uses: worst first, so the shape is learnable.
#: `INCONCLUSIVE` sits between WARN and PASS — it is not a verdict, and it must not be
#: mistaken for one in either direction.
READOUT_ORDER: tuple[str, ...] = (
    FileStatus.FAIL.value,
    FileStatus.WARN.value,
    "INCONCLUSIVE",
    FileStatus.PASS.value,
    FileStatus.NOT_INSPECTED.value,
    FileStatus.NOT_APPLICABLE.value,
)


def build_readout_segments(rows: Sequence[FileRow]) -> tuple[tuple[str, int], ...]:
    """(display status, count) in fixed worst-first order, zero counts included.

    Built from the rows rather than from `BatchSummary` on purpose. The summary is the
    canonical, exported account; the readout sits on the same screen as the table and
    must agree with it. Reading a batch as "1 Pass" while the row above says
    "Inconclusive" would be the interface arguing with itself.

    Zeros are kept so the caller can decide whether to draw them; dropping them here
    would let the order shift between batches, which is what makes a readout
    unlearnable.
    """
    counts: dict[str, int] = {}
    for row in rows:
        if not row.is_complete:
            continue
        counts[row.display_status] = counts.get(row.display_status, 0) + 1
    return tuple((name, counts.get(name, 0)) for name in READOUT_ORDER)


_GROUP_LABELS: dict[str, str] = {
    "file": "File",
    "container": "Container",
    "video": "Video",
    "audio": "Audio",
}


def _metadata_rows(result: FileResult) -> tuple[MetadataRow, ...]:
    from preflightqc.core.model import PROPERTY_PATHS

    if result.media is None:
        return ()
    rows: list[MetadataRow] = []
    for path, descriptor in PROPERTY_PATHS.items():
        # Named `reading`, not `meta`: the architecture test scans this package for
        # platform names in executable code, and `meta ` is one of them. A local variable
        # is not worth weakening that check for.
        reading = descriptor.resolve(result.media)
        provenance = reading.provenance.describe() if reading.provenance else ""
        group = _GROUP_LABELS.get(path.split(".", 1)[0], "Other")
        rows.append(
            MetadataRow(
                label=descriptor.label + (f" ({descriptor.unit})" if descriptor.unit else ""),
                value=(
                    humanise_value(reading.describe(), path)
                    if reading.is_known
                    else reading.describe()
                ),
                state=reading.state.value,
                provenance=provenance,
                group=group,
            )
        )
    return tuple(rows)


def build_file_detail(result: FileResult) -> FileDetail:
    findings = tuple(
        FindingRow(
            rule_id=f.rule_id,
            severity=f.severity.value,
            severity_rank=f.severity.rank,
            classification=f.classification.value,
            classification_label=_CLASSIFICATION_LABELS.get(
                f.classification.value, f.classification.value.replace("_", " ").title()
            ),
            property_label=f.property_label,
            property_path=f.property_path,
            detected=humanise_value(f.detected, f.property_path),
            expectation_label=split_expectation(f.expected)[0],
            expected=humanise_value(split_expectation(f.expected)[1], f.property_path),
            explanation=f.explanation,
            source_title=f.source.title,
            source_url=f.source.url,
            source_access_date=f.source.access_date,
            source_confidence=f.source.confidence,
            provenance=f.provenance or "",
            unknown_reason=f.unknown_reason or "",
        )
        for f in sorted(result.actionable_findings, key=lambda f: f.sort_key())
    )
    return FileDetail(
        name=result.display_name,
        path=str(result.path),
        status=result.status.value,
        findings=findings,
        metadata=_metadata_rows(result),
        diagnostics=tuple(result.diagnostics.notes),
        checks_passed=result.checks_passed,
        checks_total=len(result.findings),
        is_inconclusive=is_inconclusive(result),
    )
