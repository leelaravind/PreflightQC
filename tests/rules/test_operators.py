"""Phase 3 — operator semantics, including tolerance boundaries."""

from __future__ import annotations

from fractions import Fraction

import pytest

from preflightqc.rules import operators
from preflightqc.rules.operators import OperatorError


def apply(name: str, actual: object, expected: object, tol: float = 0.0, rel: bool = False) -> bool:
    return operators.get(name).apply(actual, expected, tol, rel)


class TestComparisons:
    @pytest.mark.parametrize(
        ("name", "actual", "expected", "result"),
        [
            ("eq", 30, 30, True),
            ("eq", 30, 25, False),
            ("neq", 30, 25, True),
            ("lt", 1919, 1920, True),
            ("lt", 1920, 1920, False),
            ("lte", 1920, 1920, True),
            ("lte", 1921, 1920, False),
            ("gt", 1921, 1920, True),
            ("gte", 1920, 1920, True),
            ("gte", 1919, 1920, False),
        ],
    )
    def test_scalar_comparisons(self, name: str, actual: object, expected: object, result: bool) -> None:
        assert apply(name, actual, expected) is result

    def test_ordering_a_non_numeric_value_raises(self) -> None:
        with pytest.raises(OperatorError, match="order-compare"):
            apply("lt", "progressive", 1920)


class TestMembership:
    def test_in_and_not_in(self) -> None:
        assert apply("in", "h264", ["h264", "hevc"])
        assert not apply("in", "vp9", ["h264", "hevc"])
        assert apply("not_in", "vp9", ["h264", "hevc"])

    def test_a_set_valued_actual_is_matched_by_intersection(self) -> None:
        """container.format normalises to a family; any member satisfying the rule passes."""
        assert apply("in", frozenset({"mov", "mp4", "3gp"}), ["mp4"])
        assert not apply("in", frozenset({"avi"}), ["mp4", "mov"])

    def test_an_empty_actual_set_matches_nothing(self) -> None:
        assert not apply("in", frozenset(), ["mp4"])


class TestRange:
    @pytest.mark.parametrize(
        ("value", "result"),
        [(22.9, False), (23.0, True), (30.0, True), (60.0, True), (60.1, False)],
    )
    def test_inclusive_bounds(self, value: float, result: bool) -> None:
        assert apply("range", value, {"min": 23, "max": 60}) is result

    def test_open_ended_ranges(self) -> None:
        assert apply("range", 1_000_000, {"min": 516_000})
        assert not apply("range", 500_000, {"min": 516_000})
        assert apply("range", 10, {"max": 100})

    def test_relative_tolerance_widens_both_bounds(self) -> None:
        """LinkedIn's documented 5% aspect-ratio tolerance."""
        assert apply("range", 0.55, {"min": 0.563, "max": 1.778}, tol=0.05, rel=True)
        assert apply("range", 1.85, {"min": 0.563, "max": 1.778}, tol=0.05, rel=True)
        assert not apply("range", 0.50, {"min": 0.563, "max": 1.778}, tol=0.05, rel=True)

    def test_a_non_numeric_value_raises(self) -> None:
        with pytest.raises(OperatorError, match="numeric"):
            apply("range", "progressive", {"min": 1, "max": 2})


class TestFrameRateTolerance:
    def test_drop_frame_variants_compare_equal(self) -> None:
        """The 29.97 trap: exact equality here would be a defect."""
        assert apply("eq", float(Fraction(30000, 1001)), 29.97, tol=0.01)
        assert apply("eq", float(Fraction(24000, 1001)), 23.976, tol=0.01)

    def test_distinct_rates_still_differ(self) -> None:
        assert not apply("eq", 25.0, 24.0, tol=0.01)

    def test_membership_honours_tolerance(self) -> None:
        """LinkedIn CTV's permitted frame-rate set includes drop-frame values."""
        allowed = [23.98, 24, 25, 29.97, 30]
        assert apply("in", float(Fraction(30000, 1001)), allowed, tol=0.01)
        assert not apply("in", 27.0, allowed, tol=0.01)


class TestPresenceAndPatterns:
    def test_present_and_absent(self) -> None:
        assert apply("present", "aac", None)
        assert not apply("present", None, None)
        assert apply("absent", None, None)

    def test_matches_is_anchored(self) -> None:
        assert apply("matches", "High", "High")
        assert not apply("matches", "High 4:4:4", "High")

    def test_constant_only_accepts_cfr_only(self) -> None:
        """LinkedIn CTV requires a constant frame rate."""
        assert apply("constant_only", "CFR", None)
        assert not apply("constant_only", "VFR", None)


class TestShapeValidation:
    @pytest.mark.parametrize("name", ["in", "not_in"])
    def test_list_operators_require_a_non_empty_array(self, name: str) -> None:
        with pytest.raises(OperatorError):
            operators.validate_shape(name, "mp4")
        with pytest.raises(OperatorError):
            operators.validate_shape(name, [])
        operators.validate_shape(name, ["mp4"])

    def test_range_requires_bounds(self) -> None:
        with pytest.raises(OperatorError):
            operators.validate_shape("range", {})
        operators.validate_shape("range", {"min": 1})

    @pytest.mark.parametrize("name", ["eq", "lte", "gte"])
    def test_scalar_operators_reject_containers(self, name: str) -> None:
        with pytest.raises(OperatorError):
            operators.validate_shape(name, [1, 2])
        operators.validate_shape(name, 1)

    @pytest.mark.parametrize("name", ["present", "absent", "constant_only"])
    def test_valueless_operators_reject_a_value(self, name: str) -> None:
        with pytest.raises(OperatorError):
            operators.validate_shape(name, 42)
        operators.validate_shape(name, None)

    def test_unknown_operator_lists_the_known_ones(self) -> None:
        with pytest.raises(OperatorError, match="known operators are"):
            operators.get("nope")


class TestDescriptions:
    def test_list_descriptions_read_naturally(self) -> None:
        assert operators.get("in").describe(["mp4"]) == "mp4"
        assert operators.get("in").describe(["mp4", "mov"]) == "mp4 or mov"
        assert operators.get("in").describe(["mp4", "mov", "webm"]) == "mp4, mov or webm"

    def test_range_descriptions_cover_all_three_shapes(self) -> None:
        assert operators.get("range").describe({"min": 3, "max": 900}) == "between 3 and 900"
        assert operators.get("range").describe({"min": 516000}) == "at least 516000"
        assert operators.get("range").describe({"max": 100}) == "at most 100"

    def test_integral_floats_render_without_a_trailing_zero(self) -> None:
        assert operators.get("lte").describe(1920.0) == "at most 1920"
