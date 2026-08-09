"""The single severity presentation table.

Every colour, label and icon for a severity or status comes from here. A hard-coded
severity string in a widget is a defect: it guarantees the day someone adds a state and
one panel keeps rendering the old set.

Colour is never the only signal — each entry carries a text label too, because a
red/green-only interface is unusable for a meaningful share of editors.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Style:
    label: str
    foreground: str
    background: str
    #: A short text marker so severity survives greyscale printing and colour blindness.
    marker: str


_SEVERITY: dict[str, Style] = {
    "FAIL": Style("Fail", "#ffffff", "#b3261e", "!"),
    "WARN": Style("Warning", "#ffffff", "#8a5a00", "▲"),
    "INFO": Style("Info", "#ffffff", "#40484e", "i"),
    "UNKNOWN": Style("Unknown", "#ffffff", "#5a4b7c", "?"),
}

_STATUS: dict[str, Style] = {
    "PASS": Style("Pass", "#ffffff", "#1c6b3c", "✓"),
    "WARN": Style("Warning", "#ffffff", "#8a5a00", "▲"),
    "FAIL": Style("Fail", "#ffffff", "#b3261e", "!"),
    "NOT_INSPECTED": Style("Not inspected", "#ffffff", "#5c666e", "—"),
    "NOT_APPLICABLE": Style("Not applicable", "#ffffff", "#5c666e", "—"),
}

_FALLBACK = Style("Unknown", "#ffffff", "#5c666e", "?")


def for_severity(name: str) -> Style:
    return _SEVERITY.get(name, _FALLBACK)


def for_status(name: str) -> Style:
    return _STATUS.get(name, _FALLBACK)


def badge_stylesheet(style: Style) -> str:
    return (
        f"background-color: {style.background}; color: {style.foreground};"
        " border-radius: 3px; padding: 1px 6px; font-weight: 600;"
    )
