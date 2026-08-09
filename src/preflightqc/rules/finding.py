"""A finding: the result of evaluating one rule against one file.

Findings are what the user actually reads, so every one carries the full chain needed to
justify it: what was detected, what was expected, why it matters, and which authoritative
source says so (spec 15).
"""

from __future__ import annotations

from dataclasses import dataclass

from preflightqc.rules.severity import Classification, Severity


@dataclass(frozen=True, slots=True)
class SourceReference:
    """Where a rule's authority comes from. Spec 12."""

    source_ref: str
    title: str
    url: str
    access_date: str
    confidence: str

    def describe(self) -> str:
        return f"{self.title} ({self.url}), accessed {self.access_date}, confidence {self.confidence}"


@dataclass(frozen=True, slots=True)
class Finding:
    """One rule's verdict on one file."""

    rule_id: str
    severity: Severity
    classification: Classification
    property_path: str
    property_label: str
    #: What the file actually has, rendered for display. Absent states render as words
    #: ("not present in file"), never as blank or zero.
    detected: str
    #: What the rule wants, phrased as required or recommended to match classification.
    expected: str
    explanation: str
    source: SourceReference
    #: Which inspector supplied the detected value, and from which raw field.
    provenance: str | None = None
    unit: str | None = None
    #: True when the rule passed. Retained so reports can show what was checked and
    #: satisfied, not only what failed.
    passed: bool = False
    #: Set when the rule could not be evaluated, explaining why (spec 15).
    unknown_reason: str | None = None

    @property
    def is_blocking(self) -> bool:
        return self.severity is Severity.FAIL

    def sort_key(self) -> tuple[int, str]:
        """Deterministic ordering: by severity rank, then by rule id (spec 15)."""
        return (self.severity.rank, self.rule_id)


def unknown_finding(
    *,
    rule_id: str,
    classification: Classification,
    property_path: str,
    property_label: str,
    detected: str,
    expected: str,
    explanation: str,
    source: SourceReference,
    reason: str,
    provenance: str | None = None,
    unit: str | None = None,
) -> Finding:
    """Build the UNKNOWN finding emitted when a property could not be evaluated.

    This is the single most load-bearing helper in the engine. Specification 7.1 forbids
    treating unavailable metadata as failure, and this is where that promise is kept:
    every unevaluable rule -- whatever its classification -- ends up here, at UNKNOWN.
    """
    return Finding(
        rule_id=rule_id,
        severity=Severity.UNKNOWN,
        classification=classification,
        property_path=property_path,
        property_label=property_label,
        detected=detected,
        expected=expected,
        explanation=explanation,
        source=source,
        provenance=provenance,
        unit=unit,
        passed=False,
        unknown_reason=reason,
    )
