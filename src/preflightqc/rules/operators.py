"""Rule operators.

Each operator declares the value shapes it accepts, so a preset with a mismatched
expected-value shape is rejected at load time rather than misbehaving at evaluation time.

Numeric comparisons take an explicit tolerance. There is deliberately no bare float
equality anywhere in this module: 23.976 and 24000/1001 are the same frame rate, and a
`==` between them is a defect waiting to happen.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any


class ValueShape(Enum):
    """The shape a rule's `expected` value must take for a given operator."""

    SCALAR = "scalar"
    LIST = "list"
    RANGE = "range"
    NONE = "none"


class OperatorError(ValueError):
    """Raised when an operator cannot be applied to the given values."""


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float | Fraction):
        return float(value)
    return None


def _tolerant_equal(actual: Any, expected: Any, tolerance: float, relative: bool) -> bool:
    a, b = _as_number(actual), _as_number(expected)
    if a is None or b is None:
        return bool(actual == expected)
    if tolerance <= 0:
        return a == b
    allowance = tolerance * max(abs(a), abs(b)) if relative else tolerance
    return abs(a - b) <= allowance


def _compare(actual: Any, expected: Any) -> int:
    """Three-way numeric comparison; raises for non-numeric operands."""
    a, b = _as_number(actual), _as_number(expected)
    if a is None or b is None:
        raise OperatorError(f"cannot order-compare {actual!r} and {expected!r}")
    return (a > b) - (a < b)


def _membership(actual: Any, expected: Sequence[Any], tolerance: float, relative: bool) -> bool:
    """Membership, with set-valued actuals treated as intersection.

    `container.format` normalises to a set of canonical tokens because ffprobe reports
    a container *family* ("mov,mp4,m4a"). A file satisfies a container rule when any of
    its tokens is in the allowed list.
    """
    if isinstance(actual, frozenset | set):
        return any(token in expected for token in actual)
    return any(_tolerant_equal(actual, candidate, tolerance, relative) for candidate in expected)


@dataclass(frozen=True, slots=True)
class Operator:
    """One comparison, with the value shape it requires."""

    name: str
    shape: ValueShape
    apply: Callable[[Any, Any, float, bool], bool]
    #: Template for the human-readable expected-value text.
    describe: Callable[[Any], str]


def _range_bounds(expected: Any) -> tuple[float | None, float | None]:
    if not isinstance(expected, dict):
        raise OperatorError("range operator requires an object with min and/or max")
    minimum = expected.get("min")
    maximum = expected.get("max")
    if minimum is None and maximum is None:
        raise OperatorError("range operator requires at least one of min or max")
    return (
        None if minimum is None else float(minimum),
        None if maximum is None else float(maximum),
    )


def _range_apply(actual: Any, expected: Any, tolerance: float, relative: bool) -> bool:
    minimum, maximum = _range_bounds(expected)
    value = _as_number(actual)
    if value is None:
        raise OperatorError(f"range operator needs a numeric value, got {actual!r}")
    if minimum is not None:
        lower = minimum * (1.0 - tolerance) if relative else minimum - tolerance
        if value < lower:
            return False
    if maximum is not None:
        upper = maximum * (1.0 + tolerance) if relative else maximum + tolerance
        if value > upper:
            return False
    return True


def _range_describe(expected: Any) -> str:
    minimum, maximum = _range_bounds(expected)
    if minimum is not None and maximum is not None:
        return f"between {_fmt(minimum)} and {_fmt(maximum)}"
    if minimum is not None:
        return f"at least {_fmt(minimum)}"
    return f"at most {_fmt(maximum)}"


def _fmt(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _list_describe(expected: Any) -> str:
    if not isinstance(expected, list | tuple):
        raise OperatorError("list operator requires an array")
    items = [str(item) for item in expected]
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f" or {items[-1]}"


OPERATORS: dict[str, Operator] = {
    "eq": Operator(
        "eq",
        ValueShape.SCALAR,
        lambda a, e, t, r: _tolerant_equal(a, e, t, r),
        lambda e: str(e),
    ),
    "neq": Operator(
        "neq",
        ValueShape.SCALAR,
        lambda a, e, t, r: not _tolerant_equal(a, e, t, r),
        lambda e: f"anything other than {e}",
    ),
    "in": Operator(
        "in",
        ValueShape.LIST,
        lambda a, e, t, r: _membership(a, e, t, r),
        _list_describe,
    ),
    "not_in": Operator(
        "not_in",
        ValueShape.LIST,
        lambda a, e, t, r: not _membership(a, e, t, r),
        lambda e: f"not {_list_describe(e)}",
    ),
    "range": Operator("range", ValueShape.RANGE, _range_apply, _range_describe),
    "lt": Operator(
        "lt", ValueShape.SCALAR, lambda a, e, t, r: _compare(a, e) < 0, lambda e: f"less than {_fmt(e)}"
    ),
    "lte": Operator(
        "lte", ValueShape.SCALAR, lambda a, e, t, r: _compare(a, e) <= 0, lambda e: f"at most {_fmt(e)}"
    ),
    "gt": Operator(
        "gt", ValueShape.SCALAR, lambda a, e, t, r: _compare(a, e) > 0, lambda e: f"more than {_fmt(e)}"
    ),
    "gte": Operator(
        "gte", ValueShape.SCALAR, lambda a, e, t, r: _compare(a, e) >= 0, lambda e: f"at least {_fmt(e)}"
    ),
    "present": Operator(
        "present", ValueShape.NONE, lambda a, e, t, r: a is not None, lambda e: "present"
    ),
    "absent": Operator("absent", ValueShape.NONE, lambda a, e, t, r: a is None, lambda e: "absent"),
    "matches": Operator(
        "matches",
        ValueShape.SCALAR,
        lambda a, e, t, r: _regex_match(a, e),
        lambda e: f"matching {e}",
    ),
    "constant_only": Operator(
        "constant_only",
        ValueShape.NONE,
        lambda a, e, t, r: str(a).upper() == "CFR",
        lambda e: "constant (CFR)",
    ),
}


def _regex_match(actual: Any, pattern: Any) -> bool:
    import re

    return re.fullmatch(str(pattern), str(actual)) is not None


def get(name: str) -> Operator:
    """Look up an operator, raising OperatorError for an unknown name."""
    try:
        return OPERATORS[name]
    except KeyError:
        raise OperatorError(
            f"unknown operator '{name}'; known operators are: {', '.join(sorted(OPERATORS))}"
        ) from None


def validate_shape(operator_name: str, expected: Any) -> None:
    """Check that a rule's expected value matches its operator's required shape.

    Called at preset load time so a shape mismatch rejects the preset instead of
    surfacing as a confusing runtime error on some unlucky file.
    """
    operator = get(operator_name)
    match operator.shape:
        case ValueShape.LIST:
            if not isinstance(expected, list | tuple) or not expected:
                raise OperatorError(f"operator '{operator_name}' requires a non-empty array")
        case ValueShape.RANGE:
            _range_bounds(expected)
        case ValueShape.SCALAR:
            if isinstance(expected, list | tuple | dict):
                raise OperatorError(f"operator '{operator_name}' requires a scalar value")
        case ValueShape.NONE:
            if expected not in (None, True, False):
                raise OperatorError(f"operator '{operator_name}' takes no expected value")
