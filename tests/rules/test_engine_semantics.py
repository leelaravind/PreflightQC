"""Phase 3 — engine evaluation semantics (P3-A5..A8, P3-A13).

Claim C2 from the test strategy lives here: **missing or undeterminable metadata never
produces FAIL.**
"""

from __future__ import annotations

from factories import (
    build_media,
    default_media,
    ffprobe_payload,
    mediainfo_payload,
    preset_payload,
    rule,
)
from preflightqc.rules.engine import evaluate, evaluate_rule
from preflightqc.rules.loader import build_preset
from preflightqc.rules.severity import Severity


def _single(preset_rule: dict) -> object:
    return build_preset(preset_payload(rules=[preset_rule])).rules[0]


class TestMissingMetadataNeverFails:
    def test_absent_property_yields_unknown_not_fail(self) -> None:
        """P3-A5 — the core promise of specification 7.1."""
        media = build_media(ffprobe=ffprobe_payload(video={"bit_rate": None}, bit_rate=None))
        finding = evaluate_rule(
            media,
            _single(rule(property_path="video.bitrate", operator="lte", expected=25_000_000)),
        )
        assert finding is not None
        assert finding.severity is Severity.UNKNOWN
        assert finding.severity is not Severity.FAIL

    def test_undetermined_property_yields_unknown_with_a_distinguishing_reason(self) -> None:
        """P3-A6 — 'not present' and 'could not determine' read differently."""
        media = build_media(ffprobe=ffprobe_payload(video={"field_order": "unknown"}))
        finding = evaluate_rule(
            media,
            _single(rule(property_path="video.scan_type", operator="eq", expected="progressive")),
        )
        assert finding is not None
        assert finding.severity is Severity.UNKNOWN
        assert finding.unknown_reason
        assert "heuristic" in finding.unknown_reason

    def test_a_file_with_no_audio_yields_unknown_on_audio_rules(self) -> None:
        """Spec 23 — absence of audio is never an implicit FAIL."""
        media = build_media(ffprobe=ffprobe_payload(video={}))
        finding = evaluate_rule(
            media, _single(rule(property_path="audio.codec", operator="in", expected=["aac"]))
        )
        assert finding is not None
        assert finding.severity is Severity.UNKNOWN
        assert "no audio stream" in (finding.unknown_reason or "")

    def test_documented_gap_rules_report_unknown_and_say_why(self) -> None:
        media = default_media()
        finding = evaluate_rule(
            media,
            _single(
                rule(
                    property_path="video.gop_closed",
                    operator="eq",
                    expected=True,
                    classification="HARD_REQUIREMENT",
                    severity="FAIL",
                )
            ),
        )
        assert finding is not None
        assert finding.severity is Severity.UNKNOWN
        assert "not measured by PreflightQC V1" in (finding.unknown_reason or "")

    def test_unknown_classification_never_judges(self) -> None:
        media = default_media()
        finding = evaluate_rule(
            media,
            _single(
                rule(
                    property_path="video.width",
                    operator="lte",
                    expected=10,  # the file would violate this
                    classification="UNKNOWN",
                    severity="INFO",
                    note="No authoritative specification exists for this property.",
                )
            ),
        )
        assert finding is not None
        assert finding.severity is Severity.UNKNOWN


class TestGuards:
    def test_a_false_guard_skips_the_rule_entirely(self) -> None:
        """P3-A7 — skipping, never failing."""
        media = default_media()  # SDR: transfer is bt709, not PQ/HLG
        finding = evaluate_rule(
            media,
            _single(
                rule(
                    property_path="video.bit_depth",
                    operator="gte",
                    expected=10,
                    applies_when=[
                        {
                            "property": "video.transfer_characteristics",
                            "operator": "in",
                            "expected": ["pq", "hlg"],
                        }
                    ],
                )
            ),
        )
        assert finding is None

    def test_a_true_guard_lets_the_rule_run(self) -> None:
        media = build_media(
            ffprobe=ffprobe_payload(
                video={"color_transfer": "smpte2084", "pix_fmt": "yuv420p10le"}
            )
        )
        finding = evaluate_rule(
            media,
            _single(
                rule(
                    property_path="video.bit_depth",
                    operator="gte",
                    expected=10,
                    applies_when=[
                        {
                            "property": "video.transfer_characteristics",
                            "operator": "in",
                            "expected": ["pq", "hlg"],
                        }
                    ],
                )
            ),
        )
        assert finding is not None
        assert finding.passed

    def test_a_guard_over_an_absent_property_skips_rather_than_fires(self) -> None:
        """We cannot confirm the rule applies, so we do not apply it."""
        media = build_media(
            ffprobe=ffprobe_payload(video={"color_transfer": "unknown"})
        )
        finding = evaluate_rule(
            media,
            _single(
                rule(
                    property_path="video.bit_depth",
                    operator="gte",
                    expected=10,
                    applies_when=[
                        {
                            "property": "video.transfer_characteristics",
                            "operator": "in",
                            "expected": ["pq", "hlg"],
                        }
                    ],
                )
            ),
        )
        assert finding is None


class TestConflicts:
    def test_a_conflicted_property_can_never_produce_fail(self) -> None:
        """P3-A8 — we are not confident enough about the value to reject the file."""
        media = build_media(
            ffprobe=ffprobe_payload(video={"width": 4000}),
            mediainfo=mediainfo_payload(video={"Width": "5000"}),
        )
        finding = evaluate_rule(
            media, _single(rule(property_path="video.width", operator="lte", expected=1920))
        )
        assert finding is not None
        assert finding.severity is not Severity.FAIL
        assert finding.severity is Severity.WARN

    def test_a_conflict_passes_when_any_reading_satisfies_the_rule(self) -> None:
        media = build_media(
            ffprobe=ffprobe_payload(video={"width": 1080}),
            mediainfo=mediainfo_payload(video={"Width": "4000"}),
        )
        finding = evaluate_rule(
            media, _single(rule(property_path="video.width", operator="lte", expected=1920))
        )
        assert finding is not None
        assert finding.passed

    def test_a_conflict_surfaces_both_values(self) -> None:
        media = build_media(
            ffprobe=ffprobe_payload(video={"width": 1080}),
            mediainfo=mediainfo_payload(video={"Width": "1440"}),
        )
        findings = evaluate(media, build_preset(preset_payload()))
        conflict_findings = [f for f in findings if f.rule_id.startswith("preflightqc.conflict")]
        assert conflict_findings
        assert "1080" in conflict_findings[0].detected
        assert "1440" in conflict_findings[0].detected


class TestPassingAndFailing:
    def test_a_satisfied_rule_reports_at_info_not_at_its_own_severity(self) -> None:
        """A satisfied FAIL-class rule must not itself read as a failure."""
        media = default_media()
        finding = evaluate_rule(
            media, _single(rule(property_path="video.width", operator="lte", expected=1920))
        )
        assert finding is not None
        assert finding.passed
        assert finding.severity is Severity.INFO

    def test_a_violated_hard_requirement_fails(self) -> None:
        media = build_media(ffprobe=ffprobe_payload(video={"width": 3840}))
        finding = evaluate_rule(
            media, _single(rule(property_path="video.width", operator="lte", expected=1920))
        )
        assert finding is not None
        assert not finding.passed
        assert finding.severity is Severity.FAIL

    def test_a_violated_recommendation_only_warns(self) -> None:
        """Claim C1, at evaluation time."""
        media = build_media(ffprobe=ffprobe_payload(video={"width": 3840}))
        finding = evaluate_rule(
            media,
            _single(
                rule(
                    property_path="video.width",
                    operator="lte",
                    expected=1920,
                    classification="RECOMMENDATION",
                    severity="WARN",
                )
            ),
        )
        assert finding is not None
        assert finding.severity is Severity.WARN


class TestFindingContent:
    def test_expected_text_is_phrased_as_required_for_hard_requirements(self) -> None:
        media = default_media()
        finding = evaluate_rule(
            media, _single(rule(property_path="video.width", operator="lte", expected=1920))
        )
        assert finding is not None
        assert finding.expected.startswith("required:")

    def test_expected_text_is_phrased_as_recommended_for_recommendations(self) -> None:
        """Spec 15 — a WARN must not read as a rejection."""
        media = default_media()
        finding = evaluate_rule(
            media,
            _single(
                rule(
                    property_path="video.width",
                    operator="lte",
                    expected=1920,
                    classification="RECOMMENDATION",
                    severity="WARN",
                )
            ),
        )
        assert finding is not None
        assert finding.expected.startswith("recommended:")

    def test_eligibility_text_is_phrased_as_eligibility(self) -> None:
        media = default_media()
        finding = evaluate_rule(
            media,
            _single(
                rule(
                    property_path="file.duration_seconds",
                    operator="range",
                    expected={"min": 5, "max": 90},
                    classification="ELIGIBILITY",
                    severity="WARN",
                )
            ),
        )
        assert finding is not None
        assert finding.expected.startswith("for eligibility:")

    def test_findings_carry_the_full_source_chain(self) -> None:
        """Spec 15 — every verdict must be justifiable."""
        media = default_media()
        finding = evaluate_rule(media, _single(rule()))
        assert finding is not None
        assert finding.source.url
        assert finding.source.access_date
        assert finding.source.confidence
        assert finding.rule_id

    def test_absent_values_render_as_words_not_blank(self) -> None:
        media = build_media(ffprobe=ffprobe_payload(video={"bit_rate": None}, bit_rate=None))
        finding = evaluate_rule(
            media, _single(rule(property_path="video.bitrate", operator="lte", expected=100))
        )
        assert finding is not None
        assert finding.detected.strip()
        assert finding.detected not in {"0", "", "None"}

    def test_detected_value_carries_its_unit(self) -> None:
        media = default_media()
        finding = evaluate_rule(
            media, _single(rule(property_path="video.width", operator="lte", expected=1920))
        )
        assert finding is not None
        assert "px" in finding.detected


class TestOrderingAndPurity:
    def test_findings_are_ordered_fail_warn_unknown_info(self) -> None:
        media = build_media(ffprobe=ffprobe_payload(video={"width": 3840, "bit_rate": None}))
        preset = build_preset(
            preset_payload(
                rules=[
                    rule("a.info", property_path="video.height", operator="gte", expected=1),
                    rule(
                        "b.warn",
                        property_path="video.width",
                        operator="lte",
                        expected=100,
                        classification="RECOMMENDATION",
                        severity="WARN",
                    ),
                    rule("c.fail", property_path="video.width", operator="lte", expected=1920),
                    rule("d.unknown", property_path="video.bitrate", operator="lte", expected=1),
                ]
            )
        )
        severities = [f.severity for f in evaluate(media, preset)]
        assert severities == sorted(severities, key=lambda s: s.rank)
        assert severities[0] is Severity.FAIL

    def test_evaluation_performs_no_io_no_clock_no_randomness(self, monkeypatch) -> None:
        """P3-A13 — determinism is structural, not incidental."""
        import random
        import time

        def explode(*args: object, **kwargs: object) -> object:
            raise AssertionError("the engine must not touch this")

        monkeypatch.setattr(time, "time", explode)
        monkeypatch.setattr(random, "random", explode)
        monkeypatch.setattr("builtins.open", explode)

        media = default_media()
        preset = build_preset(preset_payload())
        assert evaluate(media, preset)

    def test_disabled_rules_are_not_evaluated(self) -> None:
        media = build_media(ffprobe=ffprobe_payload(video={"width": 3840}))
        preset = build_preset(
            preset_payload(rules=[rule("off.rule", enabled=False), rule("on.rule")])
        )
        rule_ids = {f.rule_id for f in evaluate(media, preset)}
        assert "off.rule" not in rule_ids
        assert "on.rule" in rule_ids
