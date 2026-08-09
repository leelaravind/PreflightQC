"""Phase 9 — boundary coverage over every shipped rule (P9-A2, P9-A3, P9-A4).

For each FAIL rule in each shipped preset, this derives a just-inside and a
just-outside case from the rule's own expected value, and asserts the rule fires at
exactly its threshold. Deriving from the rule rather than hand-listing cases means a
rule added in Phase 4 cannot ship without boundary coverage: the coverage test fails if
any FAIL rule produces no cases.

Claims C1, C2 and C3 from the test strategy all land here, over real shipped data.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from synthetic import blank_media, boundary_values, media_satisfying_guards, media_with

from preflightqc.results.aggregate import FileStatus, deciding_severities, overall_status
from preflightqc.rules.engine import evaluate_rule
from preflightqc.rules.loader import load_catalog
from preflightqc.rules.severity import NEVER_FAIL, Classification, Severity

PRESETS_DIR = Path(__file__).resolve().parent.parent.parent / "presets"
CATALOG = load_catalog([PRESETS_DIR])

#: Rules whose boundary cannot be expressed as a single injected scalar, with the reason.
#: Recorded explicitly rather than silently skipped (test strategy section 3.5).
DERIVATION_EXCEPTIONS: dict[str, str] = {}


def failing_rules():
    for preset in CATALOG.presets:
        for rule in preset.failing_rules():
            yield preset, rule


def _cases():
    for preset, rule in failing_rules():
        if rule.rule_id in DERIVATION_EXCEPTIONS:
            continue
        for label, value, should_pass in boundary_values(rule):
            yield pytest.param(
                preset, rule, value, should_pass,
                id=f"{preset.preset_id}::{rule.rule_id}::{label}::{'pass' if should_pass else 'fail'}",
            )


class TestBoundaries:
    @pytest.mark.parametrize(("preset", "rule", "value", "should_pass"), list(_cases()))
    def test_each_failing_rule_fires_exactly_at_its_threshold(
        self, preset, rule, value, should_pass: bool
    ) -> None:
        """P9-A2 — one unit inside passes, one unit outside fails."""
        media = media_with(rule.property_path, value, base=media_satisfying_guards(rule))
        finding = evaluate_rule(media, rule)
        assert finding is not None, f"{rule.rule_id} was skipped by its own guard"
        if should_pass:
            assert finding.passed, (
                f"{rule.rule_id} rejected a value inside its documented bound: {value}"
            )
        else:
            assert not finding.passed, (
                f"{rule.rule_id} accepted a value outside its documented bound: {value}"
            )
            assert finding.severity is Severity.FAIL

    def test_every_failing_rule_has_boundary_coverage(self) -> None:
        """The check that stops a rule shipping without a test.

        A new FAIL rule either yields derivable boundary cases, or is listed as an
        explicit exception with a reason. There is no third option.
        """
        uncovered = [
            f"{preset.preset_id}:{rule.rule_id}"
            for preset, rule in failing_rules()
            if not boundary_values(rule) and rule.rule_id not in DERIVATION_EXCEPTIONS
        ]
        assert not uncovered, f"FAIL rules with no boundary coverage: {uncovered}"

    def test_the_exception_list_stays_honest(self) -> None:
        """An exception for a rule that no longer exists is a stale claim of coverage."""
        shipped = {rule.rule_id for _, rule in failing_rules()}
        stale = set(DERIVATION_EXCEPTIONS) - shipped
        assert not stale, f"exceptions listed for rules that no longer ship: {stale}"


class TestRecommendationsNeverFail:
    """Claim C1, behaviourally: a violated recommendation warns and never rejects."""

    @pytest.mark.parametrize(
        ("preset", "rule"),
        [
            pytest.param(p, r, id=f"{p.preset_id}::{r.rule_id}")
            for p in CATALOG.presets
            for r in p.enabled_rules
            if r.classification in NEVER_FAIL
        ],
    )
    def test_a_violated_recommendation_warns_and_the_file_is_not_failed(
        self, preset, rule
    ) -> None:
        """P9-A3 / spec 24.3."""
        cases = [(v, ok) for _, v, ok in boundary_values(rule) if not ok]
        if not cases:
            pytest.skip("no derivable violating value for this rule shape")
        value = cases[0][0]
        media = media_with(rule.property_path, value, base=media_satisfying_guards(rule))
        finding = evaluate_rule(media, rule)
        assert finding is not None
        assert finding.severity is not Severity.FAIL
        assert finding.severity in (Severity.WARN, Severity.UNKNOWN, Severity.INFO)

        status = overall_status(deciding_severities((finding,)))
        assert status is not FileStatus.FAIL


class TestMissingMetadataNeverFails:
    """Claim C2, over every shipped rule at once."""

    @pytest.mark.parametrize(
        "preset", CATALOG.presets, ids=lambda p: p.preset_id
    )
    def test_a_file_with_no_determinable_metadata_is_never_failed(self, preset) -> None:
        """P9-A4 / spec 24.4 — the single most important behavioural guarantee."""
        media = blank_media()
        findings = tuple(
            f for rule in preset.enabled_rules if (f := evaluate_rule(media, rule)) is not None
        )
        failures = [f for f in findings if f.severity is Severity.FAIL]
        assert not failures, (
            f"{preset.preset_id} failed a file whose metadata could not be determined: "
            f"{[f.rule_id for f in failures]}"
        )
        assert overall_status(deciding_severities(findings)) is not FileStatus.FAIL

    @pytest.mark.parametrize("preset", CATALOG.presets, ids=lambda p: p.preset_id)
    def test_undeterminable_metadata_produces_unknown_findings(self, preset) -> None:
        media = blank_media()
        findings = [
            f for rule in preset.enabled_rules if (f := evaluate_rule(media, rule)) is not None
        ]
        assert any(f.severity is Severity.UNKNOWN for f in findings)
        for finding in findings:
            if finding.severity is Severity.UNKNOWN:
                assert finding.unknown_reason, f"{finding.rule_id} says nothing about why"


class TestNoAudioStream:
    @pytest.mark.parametrize("preset", CATALOG.presets, ids=lambda p: p.preset_id)
    def test_a_video_with_no_audio_is_never_failed_for_it(self, preset) -> None:
        """P9-A7 / spec 23 — absence of audio is never an implicit failure."""
        media = blank_media()
        silent = media_with("audio.present", False, base=media)
        audio_findings = [
            f
            for rule in preset.enabled_rules
            if rule.property_path.startswith("audio.")
            and (f := evaluate_rule(silent, rule)) is not None
        ]
        failures = [f for f in audio_findings if f.severity is Severity.FAIL]
        assert not failures, f"{preset.preset_id} failed a silent file: {[f.rule_id for f in failures]}"


class TestDocumentedGaps:
    """Register gaps G-1, G-2 and G-4 must report, never judge."""

    @pytest.mark.parametrize(
        ("preset", "rule"),
        [
            pytest.param(p, r, id=f"{p.preset_id}::{r.rule_id}")
            for p in CATALOG.presets
            for r in p.enabled_rules
            if not r.measurable_offline
        ],
    )
    def test_an_unmeasurable_property_never_fails_a_file(self, preset, rule) -> None:
        media = blank_media()
        finding = evaluate_rule(media, rule)
        assert finding is not None
        assert finding.severity is not Severity.FAIL
        assert finding.severity in (Severity.UNKNOWN, Severity.INFO)

    def test_closed_gop_is_never_measured_in_v1(self) -> None:
        for preset in CATALOG.presets:
            for rule in preset.enabled_rules:
                if rule.property_path == "video.gop_closed":
                    finding = evaluate_rule(blank_media(), rule)
                    assert finding is not None
                    assert finding.severity is Severity.UNKNOWN

    def test_ctv_loudness_reports_that_it_was_not_measured(self) -> None:
        preset = CATALOG.by_id("linkedin_ctv")
        rule = next(r for r in preset.rules if r.rule_id == "linkedin_ctv.loudness")
        finding = evaluate_rule(blank_media(), rule)
        assert finding is not None
        assert finding.severity is Severity.UNKNOWN
        assert "not measured" in (finding.unknown_reason or "")


class TestUnknownClassificationRules:
    @pytest.mark.parametrize(
        ("preset", "rule"),
        [
            pytest.param(p, r, id=f"{p.preset_id}::{r.rule_id}")
            for p in CATALOG.presets
            for r in p.enabled_rules
            if r.classification is Classification.UNKNOWN
        ],
    )
    def test_an_unknown_rule_never_judges_whatever_the_value(self, preset, rule) -> None:
        """A documented gap must stay a gap even when the property is readable."""
        for _, value, _ in boundary_values(rule) or [("", "anything", True)]:
            media = media_with(rule.property_path, value, base=media_satisfying_guards(rule))
            finding = evaluate_rule(media, rule)
            assert finding is not None
            assert finding.severity is Severity.UNKNOWN
