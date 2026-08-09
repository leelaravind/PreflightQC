"""Exact geometry and frame-rate arithmetic.

Two defects this module exists to prevent:

1. **Float frame rates.** 24000/1001 is not 23.976. Storing frame rates as floats makes
   `29.97 != 29.97` a real possibility depending on how each inspector rounded. Frame
   rates are kept as `Fraction` and only converted at comparison time, with an explicit
   tolerance.

2. **Coded geometry mistaken for displayed geometry.** A file with a non-square sample
   aspect ratio, or with rotation metadata, displays at dimensions that differ from
   `width x height`. Aspect-ratio rules must evaluate against what the viewer sees --
   otherwise an anamorphic or portrait-rotated file is judged on the wrong shape.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction


class GeometryError(ValueError):
    """Raised when a geometry input cannot be interpreted."""


def parse_rational(raw: str) -> Fraction | None:
    """Parse ffprobe's "num/den" or a plain number into an exact Fraction.

    Returns None for the several ways inspectors say "no value": "0/0", "N/A", "",
    and negative or zero denominators.
    """
    text = raw.strip()
    if not text or text.upper() in {"N/A", "NAN"}:
        return None
    try:
        if "/" in text:
            num_text, den_text = text.split("/", 1)
            numerator, denominator = int(num_text), int(den_text)
            if denominator <= 0 or numerator < 0:
                return None
            if numerator == 0:
                return None
            return Fraction(numerator, denominator)
        if ":" in text:  # MediaInfo sometimes uses "16:9"
            left, right = text.split(":", 1)
            # Distinct names from the integer branch above: reusing them would make the
            # same identifier hold an int on one path and a float on another.
            left_value, right_value = float(left), float(right)
            if right_value <= 0 or left_value <= 0:
                return None
            return Fraction(left_value / right_value).limit_denominator(100000)
        value = float(text)
    except (ValueError, ZeroDivisionError):
        return None
    if not math.isfinite(value) or value <= 0:
        return None
    return Fraction(value).limit_denominator(1000000)


def normalise_rotation(degrees: float) -> int:
    """Fold an arbitrary rotation into one of 0, 90, 180, 270."""
    folded: int = int(round(degrees)) % 360
    quadrants: tuple[int, ...] = (0, 90, 180, 270)
    return min(quadrants, key=lambda candidate: abs(candidate - folded)) % 360


def swaps_axes(rotation_degrees: int) -> bool:
    """True when the rotation exchanges width and height."""
    return normalise_rotation(rotation_degrees) in (90, 270)


@dataclass(frozen=True, slots=True)
class DisplayGeometry:
    """The geometry a viewer actually sees.

    `coded_width`/`coded_height` are what the codec stores. `display_width`/
    `display_height` apply the sample aspect ratio and any rotation. Aspect-ratio rules
    evaluate against `display_aspect_ratio`.
    """

    coded_width: int
    coded_height: int
    display_width: int
    display_height: int
    display_aspect_ratio: Fraction
    sample_aspect_ratio: Fraction
    rotation_degrees: int

    @property
    def is_rotated(self) -> bool:
        return swaps_axes(self.rotation_degrees)

    @property
    def aspect_ratio_float(self) -> float:
        return float(self.display_aspect_ratio)


def compute_display_geometry(
    width: int,
    height: int,
    *,
    sample_aspect_ratio: Fraction | None = None,
    rotation_degrees: int = 0,
) -> DisplayGeometry:
    """Apply sample aspect ratio and rotation to coded dimensions.

    A SAR of None means "not signalled", which is conventionally square pixels (1:1).
    That is an assumption, but it is the assumption every player makes, and it is
    recorded as derived provenance by the caller.
    """
    if width <= 0 or height <= 0:
        raise GeometryError(f"non-positive coded dimensions: {width}x{height}")

    sar = sample_aspect_ratio if sample_aspect_ratio is not None else Fraction(1, 1)
    if sar <= 0:
        raise GeometryError(f"non-positive sample aspect ratio: {sar}")

    # Apply SAR to the horizontal axis, which is how anamorphic storage is defined.
    scaled_width = Fraction(width) * sar
    display_ratio = scaled_width / Fraction(height)

    rotation = normalise_rotation(rotation_degrees)
    if swaps_axes(rotation):
        display_ratio = 1 / display_ratio
        display_w, display_h = height, int(round(float(scaled_width)))
    else:
        display_w, display_h = int(round(float(scaled_width))), height

    return DisplayGeometry(
        coded_width=width,
        coded_height=height,
        display_width=display_w,
        display_height=display_h,
        display_aspect_ratio=display_ratio,
        sample_aspect_ratio=sar,
        rotation_degrees=rotation,
    )


def frame_rate_matches(
    actual: Fraction,
    expected: Fraction | float,
    *,
    tolerance: float = 0.01,
) -> bool:
    """Compare frame rates with an explicit absolute tolerance.

    The default 0.01 fps comfortably accommodates the drop-frame family (23.976 vs
    24000/1001, 29.97 vs 30000/1001) while still separating 25 from 24.
    """
    return abs(float(actual) - float(expected)) <= tolerance


def aspect_ratio_within(
    actual: Fraction | float,
    minimum: float | None,
    maximum: float | None,
    *,
    tolerance_fraction: float = 0.0,
) -> bool:
    """Range check for aspect ratios with a proportional tolerance.

    LinkedIn publishes an explicit 5% aspect-ratio tolerance for video ads, expressed
    here as `tolerance_fraction=0.05`, which widens both bounds proportionally.
    """
    value = float(actual)
    if minimum is not None:
        lower = minimum * (1.0 - tolerance_fraction)
        if value < lower:
            return False
    if maximum is not None:
        upper = maximum * (1.0 + tolerance_fraction)
        if value > upper:
            return False
    return True


def format_ratio(ratio: Fraction, *, max_denominator: int = 1000) -> str:
    """Render an aspect ratio the way an editor writes it, e.g. "9:16"."""
    simplified = ratio.limit_denominator(max_denominator)
    return f"{simplified.numerator}:{simplified.denominator}"


def format_frame_rate(rate: Fraction) -> str:
    """Render a frame rate exactly, preferring the familiar decimal spelling."""
    as_float = float(rate)
    if rate.denominator == 1:
        return f"{rate.numerator} fps"
    return f"{as_float:.3f} fps".replace(".000 ", " ")
