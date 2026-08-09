"""The severity model and its classification ceiling.

**This module is the product.** Specification 7 is a hard invariant: a platform
*recommendation* must never be able to reject a user's file. Everything else PreflightQC
does is in service of getting this right.

The mechanism is deliberately structural rather than procedural. Severity is not
hand-assigned per rule and then reviewed; it is *bounded by classification* and the
bound is checked when a preset is loaded (spec 7.3). A preset that violates the ceiling
is rejected whole, before any file is ever evaluated. There is no code path in which a
RECOMMENDATION emits FAIL, because such a rule cannot be loaded.
"""

from __future__ import annotations

from enum import Enum


class Severity(Enum):
    """The reporting weight of a finding. Spec 7."""

    FAIL = "FAIL"
    WARN = "WARN"
    INFO = "INFO"
    UNKNOWN = "UNKNOWN"

    @property
    def rank(self) -> int:
        """Ordering for display: FAIL, WARN, UNKNOWN, INFO (spec 15)."""
        return _DISPLAY_RANK[self]


_DISPLAY_RANK: dict[Severity, int] = {
    Severity.FAIL: 0,
    Severity.WARN: 1,
    Severity.UNKNOWN: 2,
    Severity.INFO: 3,
}


class Classification(Enum):
    """The evidentiary strength of a rule's basis. Spec 7.3.

    This is a statement about the *source*, not about the file. It is what the register
    records, and it is what bounds severity.
    """

    HARD_REQUIREMENT = "HARD_REQUIREMENT"
    """An authoritative hard requirement for the selected surface."""

    DOCUMENTED_LIMIT = "DOCUMENTED_LIMIT"
    """A documented platform limit for the selected surface."""

    RECOMMENDATION = "RECOMMENDATION"
    """An official recommendation. Departing from it is not grounds for rejection."""

    BEST_PRACTICE = "BEST_PRACTICE"
    """Published guidance weaker than a recommendation."""

    ELIGIBILITY = "ELIGIBILITY"
    """A discovery or distribution condition, not an acceptance requirement."""

    UNKNOWN = "UNKNOWN"
    """Insufficient source authority, or the property is not measurable in V1."""


#: The maximum severity each classification may ever produce.
#:
#: Read this table as the specification's 7.3 promise in executable form. The three
#: never-FAIL classifications are the reason PreflightQC can be trusted; UNKNOWN is
#: capped at INFO so that "we do not know" can never read as "your file is wrong".
MAX_SEVERITY: dict[Classification, Severity] = {
    Classification.HARD_REQUIREMENT: Severity.FAIL,
    Classification.DOCUMENTED_LIMIT: Severity.FAIL,
    Classification.RECOMMENDATION: Severity.WARN,
    Classification.BEST_PRACTICE: Severity.WARN,
    Classification.ELIGIBILITY: Severity.WARN,
    Classification.UNKNOWN: Severity.INFO,
}

#: Classifications that may never produce FAIL, named for use in tests and messages.
NEVER_FAIL = frozenset(
    {Classification.RECOMMENDATION, Classification.BEST_PRACTICE, Classification.ELIGIBILITY}
)

#: How permissive each severity is, for the ceiling comparison. Lower is more severe.
_PERMISSIVENESS: dict[Severity, int] = {
    Severity.FAIL: 0,
    Severity.WARN: 1,
    Severity.INFO: 2,
    Severity.UNKNOWN: 2,
}


def is_permitted(classification: Classification, severity: Severity) -> bool:
    """Whether a classification may carry this severity.

    UNKNOWN severity is always permitted: a rule may always report that it could not
    determine something, regardless of how strong its source is.
    """
    if severity is Severity.UNKNOWN:
        return True
    ceiling = MAX_SEVERITY[classification]
    return _PERMISSIVENESS[severity] >= _PERMISSIVENESS[ceiling]


def cap(classification: Classification, severity: Severity) -> Severity:
    """Reduce a severity to the classification's ceiling.

    Used at evaluation time as a second line of defence -- for example when a CONFLICTED
    metadata field caps an otherwise-FAIL rule at WARN. The loader has already rejected
    anything that would need capping here, so this should be a no-op in practice.
    """
    if is_permitted(classification, severity):
        return severity
    return MAX_SEVERITY[classification]


def ceiling_violation_message(rule_id: str, classification: Classification, severity: Severity) -> str:
    """The message shown when a preset breaks the ceiling. Names the offending rule."""
    return (
        f"rule '{rule_id}' declares severity {severity.value} but is classified "
        f"{classification.value}, whose maximum permitted severity is "
        f"{MAX_SEVERITY[classification].value}. "
        "Specification 7.1 forbids converting a recommendation into a failure."
    )
