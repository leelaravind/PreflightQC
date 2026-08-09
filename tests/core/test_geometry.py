"""Phase 2 — exact geometry and frame-rate arithmetic (P2-A4, P2-A5, P2-A6)."""

from __future__ import annotations

from fractions import Fraction

import pytest

from preflightqc.core.geometry import (
    GeometryError,
    aspect_ratio_within,
    compute_display_geometry,
    format_ratio,
    frame_rate_matches,
    normalise_rotation,
    parse_rational,
    swaps_axes,
)


class TestRationals:
    def test_drop_frame_rates_round_trip_exactly(self) -> None:
        """P2-A4 — 24000/1001 must stay exact, not become 23.976."""
        rate = parse_rational("24000/1001")
        assert rate == Fraction(24000, 1001)
        assert rate.denominator == 1001  # still a rational, not collapsed to float

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("30/1", Fraction(30)),
            ("30000/1001", Fraction(30000, 1001)),
            ("25", Fraction(25)),
            ("16:9", Fraction(16, 9)),
            ("1:1", Fraction(1)),
        ],
    )
    def test_parses_the_shapes_inspectors_emit(self, text: str, expected: Fraction) -> None:
        assert parse_rational(text) == expected

    @pytest.mark.parametrize("text", ["0/0", "N/A", "", "  ", "0", "-5", "abc", "1/0"])
    def test_absent_markers_parse_to_none_not_zero(self, text: str) -> None:
        """Every way an inspector says 'no value' must become None, never 0."""
        assert parse_rational(text) is None


class TestFrameRateComparison:
    def test_drop_frame_variants_compare_equal_within_tolerance(self) -> None:
        assert frame_rate_matches(Fraction(24000, 1001), 23.976)
        assert frame_rate_matches(Fraction(30000, 1001), 29.97)
        assert frame_rate_matches(Fraction(60000, 1001), 59.94)

    def test_genuinely_different_rates_do_not_compare_equal(self) -> None:
        assert not frame_rate_matches(Fraction(25), 24)
        assert not frame_rate_matches(Fraction(30), 29.97)


class TestDisplayGeometry:
    def test_square_pixels_leave_geometry_unchanged(self) -> None:
        geometry = compute_display_geometry(1920, 1080)
        assert (geometry.display_width, geometry.display_height) == (1920, 1080)
        assert geometry.display_aspect_ratio == Fraction(16, 9)

    def test_anamorphic_sar_changes_the_displayed_ratio(self) -> None:
        """P2-A5 — a non-square SAR means width/height is the wrong shape to judge."""
        geometry = compute_display_geometry(1440, 1080, sample_aspect_ratio=Fraction(4, 3))
        assert geometry.display_aspect_ratio == Fraction(16, 9)
        assert geometry.display_aspect_ratio != Fraction(1440, 1080)
        assert geometry.display_width == 1920

    @pytest.mark.parametrize("rotation", [90, 270])
    def test_rotation_swaps_displayed_dimensions(self, rotation: int) -> None:
        """P2-A6 — a portrait-rotated landscape file displays portrait."""
        geometry = compute_display_geometry(1920, 1080, rotation_degrees=rotation)
        assert (geometry.display_width, geometry.display_height) == (1080, 1920)
        assert geometry.display_aspect_ratio == Fraction(9, 16)
        assert geometry.is_rotated

    @pytest.mark.parametrize("rotation", [0, 180])
    def test_flat_rotations_do_not_swap_axes(self, rotation: int) -> None:
        geometry = compute_display_geometry(1920, 1080, rotation_degrees=rotation)
        assert (geometry.display_width, geometry.display_height) == (1920, 1080)
        assert not geometry.is_rotated

    def test_coded_dimensions_are_retained_alongside_displayed(self) -> None:
        geometry = compute_display_geometry(1440, 1080, sample_aspect_ratio=Fraction(4, 3))
        assert (geometry.coded_width, geometry.coded_height) == (1440, 1080)

    @pytest.mark.parametrize(("width", "height"), [(0, 1080), (1920, 0), (-1, 100)])
    def test_non_positive_dimensions_raise(self, width: int, height: int) -> None:
        with pytest.raises(GeometryError):
            compute_display_geometry(width, height)


class TestRotationNormalisation:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [(0, 0), (90, 90), (-90, 270), (270, 270), (360, 0), (450, 90), (-270, 90)],
    )
    def test_arbitrary_angles_fold_into_the_four_quadrants(self, raw: int, expected: int) -> None:
        assert normalise_rotation(raw) == expected

    def test_only_quarter_turns_swap_axes(self) -> None:
        assert swaps_axes(90) and swaps_axes(270)
        assert not swaps_axes(0) and not swaps_axes(180)


class TestAspectRatioRange:
    def test_tolerance_widens_both_bounds_proportionally(self) -> None:
        """LinkedIn publishes an explicit 5% aspect-ratio tolerance for video ads."""
        assert aspect_ratio_within(0.55, 0.563, 1.778, tolerance_fraction=0.05)
        assert aspect_ratio_within(1.85, 0.563, 1.778, tolerance_fraction=0.05)
        assert not aspect_ratio_within(0.50, 0.563, 1.778, tolerance_fraction=0.05)
        assert not aspect_ratio_within(1.90, 0.563, 1.778, tolerance_fraction=0.05)

    def test_without_tolerance_the_bounds_are_exact(self) -> None:
        assert aspect_ratio_within(0.563, 0.563, 1.778)
        assert not aspect_ratio_within(0.562, 0.563, 1.778)

    def test_open_ended_ranges_are_supported(self) -> None:
        assert aspect_ratio_within(99.0, 0.01, None)
        assert aspect_ratio_within(0.001, None, 10.0)


def test_format_ratio_renders_the_way_editors_write_it() -> None:
    assert format_ratio(Fraction(9, 16)) == "9:16"
    assert format_ratio(Fraction(16, 9)) == "16:9"
    assert format_ratio(Fraction(1, 1)) == "1:1"
