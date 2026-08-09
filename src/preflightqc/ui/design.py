"""Design tokens. Every colour, size and type decision in the product lives here.

Qt-free on purpose. Tokens defined in a module that imports Qt can only be checked by
launching a window; tokens defined here can be asserted headlessly — which is how the
contrast ratios in `docs/design/UI-DESIGN-SPEC-V1.md` §2.4 are *computed* rather than
claimed. A palette edit that drops a pair below its WCAG threshold fails the suite.

A hex literal anywhere else in the UI package is a defect, and a test says so.

Authority: docs/design/UI-DESIGN-SPEC-V1.md
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Surfaces and text
#
# Near-neutral graphite with a slight cool cast, the way measurement equipment is
# finished. This is not "dark mode" as a style: it is the register of the applications
# this one sits beside on an editor's desk, in a room deliberately kept dim.
# ---------------------------------------------------------------------------

SURFACE_SUNKEN = "#14171A"
SURFACE_BASE = "#1B1F23"
SURFACE_RAISED = "#232830"
SURFACE_OVERLAY = "#2B313A"

BORDER_SUBTLE = "#2E343C"
BORDER_STRONG = "#3B434D"

TEXT_PRIMARY = "#E6EAEE"
TEXT_SECONDARY = "#A7B0B9"
TEXT_MUTED = "#7A848E"
TEXT_ON_ACCENT = "#0E1417"

#: The single interactive accent, taken from a vectorscope graticule rather than from a
#: brand palette. It is the only saturated colour that is not a severity, so "you can act
#: on this" never competes with "this is a verdict".
ACCENT = "#4FB6C4"
ACCENT_HOVER = "#63C6D3"
ACCENT_PRESSED = "#3C97A4"
ACCENT_SUBTLE = "#16323A"

# ---------------------------------------------------------------------------
# Typography
#
# No typeface is bundled. Shipping a display face for personality would add a licence
# obligation to a product whose licensing gate is the hardest part of its release.
# ---------------------------------------------------------------------------

FONT_UI = '"Segoe UI Variable Text", "Segoe UI", "Inter", sans-serif'
FONT_MONO = '"Cascadia Mono", "Consolas", "Courier New", monospace'

TYPE_DISPLAY = 20.0
TYPE_TITLE = 13.0
TYPE_HEADING = 10.5
TYPE_BODY = 9.0
TYPE_LABEL = 8.5
TYPE_CAPTION = 8.0

WEIGHT_REGULAR = 400
WEIGHT_MEDIUM = 500
WEIGHT_SEMIBOLD = 600

# ---------------------------------------------------------------------------
# Spacing, radius, dimension
# ---------------------------------------------------------------------------

#: A spacing value not on this scale is a bug.
SPACE = (2, 4, 6, 8, 12, 16, 20, 24, 32, 40)

SPACE_XXS, SPACE_XS, SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL, SPACE_2XL = 2, 4, 6, 8, 12, 16, 20

RADIUS_CHIP = 2
RADIUS_CONTROL = 3
RADIUS_PANEL = 4

CONTROL_HEIGHT = 28
PRIMARY_HEIGHT = 30
TOOLBAR_HEIGHT = 46
ROW_HEIGHT = 28
READOUT_HEIGHT = 26

#: Below this the toolbar clips. Audit finding F-36.
MIN_WINDOW_WIDTH = 960
MIN_WINDOW_HEIGHT = 640
DEFAULT_WINDOW_WIDTH = 1240
DEFAULT_WINDOW_HEIGHT = 820

FOCUS_RING_WIDTH = 2

# ---------------------------------------------------------------------------
# Severity presentation
#
# Meaning is fixed by the specification and is not a design decision. What IS a design
# decision is that three independent signals always travel together -- marker, label and
# colour -- so removing any one of them still leaves the state readable.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StatusTone:
    """One severity or status, in every form the interface needs it."""

    label: str
    #: A text glyph, so there is no icon font, no asset pipeline and no 2x variant.
    marker: str
    foreground: str
    background: str
    border: str

    @property
    def chip_text(self) -> str:
        return f"{self.marker} {self.label}"


PASS_TONE = StatusTone("Pass", "✓", "#6FD08C", "#17331F", "#2C6B41")
WARN_TONE = StatusTone("Warning", "▲", "#E8B44A", "#3A2E12", "#7A5C1B")
FAIL_TONE = StatusTone("Fail", "✕", "#F2726A", "#3B1B1A", "#8C332D")
INFO_TONE = StatusTone("Info", "i", "#9AA6B2", SURFACE_RAISED, BORDER_STRONG)
UNKNOWN_TONE = StatusTone("Unknown", "?", "#B79BE0", "#2A2338", "#574577")
NEUTRAL_TONE = StatusTone("Not inspected", "—", TEXT_MUTED, SURFACE_RAISED, BORDER_STRONG)

#: A pass that could not actually check anything. Not a sixth severity and not a status:
#: a presentation qualifier, borrowing the UNKNOWN family because that is what it means.
#: See UI-DESIGN-SPEC-V1.md §2.3 and audit finding F-1.
INCONCLUSIVE_TONE = StatusTone("Inconclusive", "?", "#B79BE0", "#2A2338", "#574577")

# ---------------------------------------------------------------------------
# Contrast
# ---------------------------------------------------------------------------

#: WCAG 2.1 AA. Body text must clear the first; large text and non-text boundaries the
#: second.
CONTRAST_BODY = 4.5
CONTRAST_LARGE = 3.0


def _channel(value: int) -> float:
    fraction = value / 255.0
    return fraction / 12.92 if fraction <= 0.04045 else ((fraction + 0.055) / 1.055) ** 2.4


def relative_luminance(colour: str) -> float:
    """WCAG relative luminance of a `#rrggbb` colour."""
    text = colour.lstrip("#")
    if len(text) != 6:
        raise ValueError(f"expected #rrggbb, got {colour!r}")
    red, green, blue = (int(text[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(foreground: str, background: str) -> float:
    """WCAG 2.1 contrast ratio, 1.0 to 21.0."""
    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


#: Pairs that must hold for the interface to be readable, checked by test.
#: (foreground, background, minimum ratio, description)
REQUIRED_CONTRAST: tuple[tuple[str, str, float, str], ...] = (
    (TEXT_PRIMARY, SURFACE_BASE, CONTRAST_BODY, "body text on panels"),
    (TEXT_PRIMARY, SURFACE_SUNKEN, CONTRAST_BODY, "body text on the window"),
    (TEXT_PRIMARY, SURFACE_RAISED, CONTRAST_BODY, "body text on the toolbar"),
    (TEXT_PRIMARY, SURFACE_OVERLAY, CONTRAST_BODY, "body text on hover"),
    (TEXT_SECONDARY, SURFACE_BASE, CONTRAST_BODY, "labels on panels"),
    (TEXT_SECONDARY, SURFACE_RAISED, CONTRAST_BODY, "column headers"),
    (TEXT_MUTED, SURFACE_BASE, CONTRAST_LARGE, "provenance captions"),
    (TEXT_ON_ACCENT, ACCENT, CONTRAST_BODY, "primary button label"),
    (ACCENT, SURFACE_BASE, CONTRAST_LARGE, "focus ring against panels"),
    (ACCENT, SURFACE_SUNKEN, CONTRAST_LARGE, "focus ring against the window"),
    (TEXT_PRIMARY, ACCENT_SUBTLE, CONTRAST_BODY, "text in a selected row"),
    (PASS_TONE.foreground, PASS_TONE.background, CONTRAST_BODY, "PASS chip"),
    (WARN_TONE.foreground, WARN_TONE.background, CONTRAST_BODY, "WARN chip"),
    (FAIL_TONE.foreground, FAIL_TONE.background, CONTRAST_BODY, "FAIL chip"),
    (INFO_TONE.foreground, INFO_TONE.background, CONTRAST_BODY, "INFO chip"),
    (UNKNOWN_TONE.foreground, UNKNOWN_TONE.background, CONTRAST_BODY, "UNKNOWN chip"),
    (NEUTRAL_TONE.foreground, NEUTRAL_TONE.background, CONTRAST_LARGE, "neutral chip"),
    (PASS_TONE.foreground, SURFACE_BASE, CONTRAST_BODY, "PASS text on a panel"),
    (WARN_TONE.foreground, SURFACE_BASE, CONTRAST_BODY, "WARN text on a panel"),
    (FAIL_TONE.foreground, SURFACE_BASE, CONTRAST_BODY, "FAIL text on a panel"),
    (UNKNOWN_TONE.foreground, SURFACE_BASE, CONTRAST_BODY, "UNKNOWN text on a panel"),
)

#: Every tone the interface can show. Two invariants hold across this set, and they are
#: the ones that actually protect a user who cannot separate the hues:
#:
#:   * markers are unique
#:   * labels are unique
#:
#: Deliberately NOT asserted: a luminance-contrast floor *between* tone foregrounds. That
#: metric measures lightness difference, not distinguishability — PASS green and WARN
#: amber sit at a ratio of 1.00 because they are equally light, while being about as
#: distinguishable as two colours can be. Testing it would fail a good palette and pass a
#: bad one. The marker and the label are the guarantee; colour is reinforcement.
DISTINCT_TONES: tuple[StatusTone, ...] = (
    PASS_TONE,
    WARN_TONE,
    FAIL_TONE,
    INFO_TONE,
    UNKNOWN_TONE,
    NEUTRAL_TONE,
)
