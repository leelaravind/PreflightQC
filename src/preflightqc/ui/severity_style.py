"""The single severity presentation table.

Every colour, label and marker for a severity or status resolves through here, and the
values themselves live in `design.py`. A hard-coded severity string in a widget is a
defect: it guarantees the day someone adds a state and one panel keeps rendering the old
set.

Colour is never the only signal. Each tone carries a text label and a text marker as
well, because a red/green-only interface is unusable for a meaningful share of editors —
and because a status column that survives a greyscale print is worth more than one that
does not.
"""

from __future__ import annotations

from preflightqc.ui import design
from preflightqc.ui.design import StatusTone

#: Kept as an alias so existing callers and tests read naturally.
Style = StatusTone

_SEVERITY: dict[str, StatusTone] = {
    "FAIL": design.FAIL_TONE,
    "WARN": design.WARN_TONE,
    "INFO": design.INFO_TONE,
    "UNKNOWN": design.UNKNOWN_TONE,
}

_STATUS: dict[str, StatusTone] = {
    "PASS": design.PASS_TONE,
    "WARN": design.WARN_TONE,
    "FAIL": design.FAIL_TONE,
    "NOT_INSPECTED": design.NEUTRAL_TONE,
    "NOT_APPLICABLE": design.NEUTRAL_TONE,
    #: Not a FileStatus. The presentation-only qualifier the interface shows when the
    #: inspection established nothing; see `for_row`.
    "INCONCLUSIVE": design.INCONCLUSIVE_TONE,
}

_FALLBACK = design.NEUTRAL_TONE


def for_severity(name: str) -> StatusTone:
    return _SEVERITY.get(name, _FALLBACK)


def for_status(name: str) -> StatusTone:
    return _STATUS.get(name, _FALLBACK)


def for_row(status: str, *, inconclusive: bool = False) -> StatusTone:
    """The tone for a table row, taking the inconclusive qualifier into account.

    An inconclusive result keeps its canonical status everywhere it is recorded — the
    export, the report, the aggregate counters — but must not *look* like a verdict the
    tool actually reached. A zero-byte file that renders as a confident green "Pass" is
    the single most misleading thing this interface could do.

    See UI-DESIGN-SPEC-V1.md §2.3 and audit finding F-1.
    """
    if inconclusive:
        return design.INCONCLUSIVE_TONE
    return for_status(status)


def badge_stylesheet(style: StatusTone) -> str:
    """Inline CSS for a chip inside a rich-text view."""
    return (
        f"background-color: {style.background}; color: {style.foreground};"
        f" border: 1px solid {style.border};"
        f" border-radius: {design.RADIUS_CHIP}px; padding: 1px 6px;"
        f" font-weight: {design.WEIGHT_SEMIBOLD};"
    )
