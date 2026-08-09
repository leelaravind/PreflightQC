"""The severity invariant — layer 1 of 3 (test strategy section 4).

This is the most important test file in the product. Specification 7.1 forbids
converting a platform recommendation into a failure, and the mechanism that makes that
unviolatable is the load-time ceiling. If these tests pass, no preset in existence can
make a RECOMMENDATION emit FAIL, because such a preset cannot be loaded.
"""

from __future__ import annotations

import pytest

from factories import preset_payload, rule
from preflightqc.rules import severity as sev
from preflightqc.rules.loader import PresetError, build_preset
from preflightqc.rules.severity import Classification, Severity

ACCEPT = "accept"
REJECT = "reject"

#: The complete ceiling table from the test strategy, expressed as data.
CEILING_TABLE: list[tuple[Classification, Severity, str]] = [
    (Classification.HARD_REQUIREMENT, Severity.FAIL, ACCEPT),
    (Classification.HARD_REQUIREMENT, Severity.WARN, ACCEPT),
    (Classification.HARD_REQUIREMENT, Severity.INFO, ACCEPT),
    (Classification.HARD_REQUIREMENT, Severity.UNKNOWN, ACCEPT),
    (Classification.DOCUMENTED_LIMIT, Severity.FAIL, ACCEPT),
    (Classification.DOCUMENTED_LIMIT, Severity.WARN, ACCEPT),
    (Classification.DOCUMENTED_LIMIT, Severity.INFO, ACCEPT),
    (Classification.DOCUMENTED_LIMIT, Severity.UNKNOWN, ACCEPT),
    (Classification.RECOMMENDATION, Severity.FAIL, REJECT),
    (Classification.RECOMMENDATION, Severity.WARN, ACCEPT),
    (Classification.RECOMMENDATION, Severity.INFO, ACCEPT),
    (Classification.RECOMMENDATION, Severity.UNKNOWN, ACCEPT),
    (Classification.BEST_PRACTICE, Severity.FAIL, REJECT),
    (Classification.BEST_PRACTICE, Severity.WARN, ACCEPT),
    (Classification.BEST_PRACTICE, Severity.INFO, ACCEPT),
    (Classification.BEST_PRACTICE, Severity.UNKNOWN, ACCEPT),
    (Classification.ELIGIBILITY, Severity.FAIL, REJECT),
    (Classification.ELIGIBILITY, Severity.WARN, ACCEPT),
    (Classification.ELIGIBILITY, Severity.INFO, ACCEPT),
    (Classification.ELIGIBILITY, Severity.UNKNOWN, ACCEPT),
    (Classification.UNKNOWN, Severity.FAIL, REJECT),
    (Classification.UNKNOWN, Severity.WARN, REJECT),
    (Classification.UNKNOWN, Severity.INFO, ACCEPT),
    (Classification.UNKNOWN, Severity.UNKNOWN, ACCEPT),
]


@pytest.mark.parametrize(("classification", "severity", "outcome"), CEILING_TABLE)
def test_ceiling_table_is_enforced_at_load(
    classification: Classification, severity: Severity, outcome: str
) -> None:
    payload = preset_payload(
        rules=[rule(classification=classification.value, severity=severity.value)]
    )
    if outcome == ACCEPT:
        preset = build_preset(payload)
        assert preset.rules[0].severity is severity
    else:
        with pytest.raises(PresetError) as exc:
            build_preset(payload)
        # The message must name the offending rule so a user can act on it.
        assert "test.rule" in str(exc.value)


@pytest.mark.parametrize(("classification", "severity", "outcome"), CEILING_TABLE)
def test_is_permitted_matches_the_table(
    classification: Classification, severity: Severity, outcome: str
) -> None:
    assert sev.is_permitted(classification, severity) is (outcome == ACCEPT)


@pytest.mark.parametrize("classification", sorted(sev.NEVER_FAIL, key=lambda c: c.value))
def test_never_fail_classifications_cannot_be_loaded_as_fail(classification: Classification) -> None:
    with pytest.raises(PresetError, match="forbids converting a recommendation"):
        build_preset(
            preset_payload(rules=[rule(classification=classification.value, severity="FAIL")])
        )


def test_a_single_bad_rule_rejects_the_whole_preset() -> None:
    """Rejection is all-or-nothing: a preset must never partially load (spec 23)."""
    payload = preset_payload(
        rules=[
            rule("good.one", classification="HARD_REQUIREMENT", severity="FAIL"),
            rule("bad.one", classification="RECOMMENDATION", severity="FAIL"),
            rule("good.two", classification="RECOMMENDATION", severity="WARN"),
        ]
    )
    with pytest.raises(PresetError) as exc:
        build_preset(payload)
    assert "bad.one" in str(exc.value)


def test_cap_reduces_to_the_ceiling() -> None:
    assert sev.cap(Classification.RECOMMENDATION, Severity.FAIL) is Severity.WARN
    assert sev.cap(Classification.ELIGIBILITY, Severity.FAIL) is Severity.WARN
    assert sev.cap(Classification.HARD_REQUIREMENT, Severity.FAIL) is Severity.FAIL


def test_unknown_severity_is_always_permitted() -> None:
    """A rule may always say it could not determine something, whatever its source."""
    for classification in Classification:
        assert sev.is_permitted(classification, Severity.UNKNOWN)


def test_max_severity_table_covers_every_classification() -> None:
    assert set(sev.MAX_SEVERITY) == set(Classification)


def test_display_ordering_is_fail_warn_unknown_info() -> None:
    """Spec 15 display order."""
    order = sorted(Severity, key=lambda s: s.rank)
    assert order == [Severity.FAIL, Severity.WARN, Severity.UNKNOWN, Severity.INFO]
