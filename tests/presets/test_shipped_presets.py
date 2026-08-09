"""Phase 4 — assertions over the shipped preset data (P4-A1..A11).

Claims C1 and C3 from the test strategy are enforced here, over the real data that
ships, rather than over a fixture.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import ClassVar

import pytest

from preflightqc.rules.document import PresetDocument
from preflightqc.rules.loader import load_catalog
from preflightqc.rules.severity import NEVER_FAIL, Classification, Severity

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRESETS_DIR = REPO_ROOT / "presets"
REGISTER = REPO_ROOT / "docs" / "sources" / "SOURCE-REGISTER.md"

EXPECTED_PRESET_IDS = {
    "ig_reels",
    "ig_stories",
    "ig_feed",
    "tiktok_content_posting_api",
    "tiktok_studio_web",
    "tiktok_infeed_auction_nonspark",
    "tiktok_topview_reservation",
    "youtube_standard",
    "youtube_shorts",
    "linkedin_organic",
    "linkedin_video_ads",
    "linkedin_ctv",
}


@pytest.fixture(scope="module")
def catalog():
    return load_catalog([PRESETS_DIR])


@pytest.fixture(scope="module")
def presets(catalog) -> tuple[PresetDocument, ...]:
    return catalog.presets


def all_rules(presets: tuple[PresetDocument, ...]):
    for preset in presets:
        for rule in preset.rules:
            yield preset, rule


class TestCatalogLoads:
    def test_every_expected_preset_loads(self, catalog) -> None:
        """P4-A1."""
        assert not catalog.rejected, catalog.rejected
        assert {p.preset_id for p in catalog.presets} == EXPECTED_PRESET_IDS

    def test_all_four_platform_families_are_present(self, presets) -> None:
        assert {p.platform for p in presets} == {
            "Meta / Instagram",
            "TikTok",
            "YouTube",
            "LinkedIn",
        }


class TestSeverityInvariantGlobal:
    def test_no_shipped_rule_converts_a_recommendation_into_a_failure(self, presets) -> None:
        """P4-A2 / spec AC-07 — the headline guarantee, over real shipped data."""
        offenders = [
            f"{preset.preset_id}:{rule.rule_id} ({rule.classification.value})"
            for preset, rule in all_rules(presets)
            if rule.classification in NEVER_FAIL and rule.severity is Severity.FAIL
        ]
        assert not offenders, f"rules that would reject a file on a recommendation: {offenders}"

    def test_no_unknown_classification_carries_fail_or_warn(self, presets) -> None:
        offenders = [
            f"{preset.preset_id}:{rule.rule_id}"
            for preset, rule in all_rules(presets)
            if rule.classification is Classification.UNKNOWN
            and rule.severity in (Severity.FAIL, Severity.WARN)
        ]
        assert not offenders

    def test_every_failing_rule_has_a_high_confidence_source(self, presets) -> None:
        """A FAIL must never rest on a medium- or low-confidence reading."""
        offenders = [
            f"{preset.preset_id}:{rule.rule_id} ({rule.source.confidence})"
            for preset, rule in all_rules(presets)
            if rule.severity is Severity.FAIL and rule.source.confidence != "HIGH"
        ]
        assert not offenders, f"low-confidence rules that would reject a file: {offenders}"


class TestSourceTraceability:
    def test_every_rule_carries_a_complete_source_chain(self, presets) -> None:
        """P4-A4 / claim C3."""
        for preset, rule in all_rules(presets):
            where = f"{preset.preset_id}:{rule.rule_id}"
            assert rule.explanation.strip(), where
            assert rule.source.url.strip(), where
            assert rule.source.access_date.strip(), where
            assert rule.source.confidence in {"HIGH", "MEDIUM", "LOW"}, where
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", rule.last_verified_date), where

    def test_every_source_ref_appears_in_the_register(self, presets) -> None:
        """P4-A3 — the chain from a finding to an authoritative source must not break."""
        register_text = REGISTER.read_text(encoding="utf-8")
        missing = {
            rule.source.source_ref
            for _, rule in all_rules(presets)
            if rule.source.source_ref not in register_text
        }
        assert not missing, f"source refs absent from SOURCE-REGISTER.md: {sorted(missing)}"

    def test_every_source_url_appears_in_the_register(self, presets) -> None:
        # The register writes some URLs without a scheme or "www.", so both sides are
        # normalised to host+path before comparison. What matters is that the source a
        # rule cites is the source the register actually recorded.
        def normalise(url: str) -> str:
            return re.sub(r"^(https?://)?(www\.)?", "", url.strip()).rstrip("/").lower()

        register_text = REGISTER.read_text(encoding="utf-8").lower()
        missing = {
            rule.source.url
            for _, rule in all_rules(presets)
            if normalise(rule.source.url) not in register_text
        }
        assert not missing, f"source URLs absent from SOURCE-REGISTER.md: {sorted(missing)}"


class TestForbiddenValues:
    """P4-A8 — third-party numbers the register explicitly rejects must never ship."""

    FORBIDDEN: ClassVar[dict[str, str]] = {
        "200000000": "LinkedIn ads 200 MB (third-party blogs; LinkedIn states 500 MB)",
        "512000000000": "YouTube 512 GB (third-party; YouTube states 256 GB)",
        "72000000": "TikTok mobile 72 MB cap (third-party only)",
        "287600000": "TikTok mobile 287.6 MB cap (third-party only)",
    }

    def test_no_preset_contains_a_rejected_third_party_figure(self) -> None:
        offenders: list[str] = []
        for path in sorted(PRESETS_DIR.rglob("*.json")):
            text = path.read_text(encoding="utf-8")
            offenders.extend(
                f"{path.name}: {why}" for value, why in self.FORBIDDEN.items() if value in text
            )
        assert not offenders, offenders

    def test_instagram_reels_uses_the_authoritative_file_size(self, catalog) -> None:
        """300 MB from the API, not the 100 MB some integrator docs cite."""
        preset = catalog.by_id("ig_reels")
        rule = next(r for r in preset.rules if r.rule_id == "ig_reels.file_size")
        assert rule.expected == 300_000_000

    def test_no_loudness_target_is_imported_as_a_measurable_rule(self, presets) -> None:
        """Meta and TikTok publish no loudness target; LinkedIn's cannot be measured in V1."""
        for preset, rule in all_rules(presets):
            if "loudness" in rule.rule_id or "lufs" in rule.rule_id.lower():
                assert rule.classification is Classification.UNKNOWN, (
                    f"{preset.preset_id}:{rule.rule_id} must not judge loudness in V1"
                )


class TestVerbatimValues:
    """Machine checks on the highest-risk transcriptions (test strategy section 6)."""

    @pytest.mark.parametrize(
        ("preset_id", "rule_id", "expected"),
        [
            ("ig_reels", "ig_reels.file_size", 300_000_000),
            ("ig_reels", "ig_reels.duration", {"min": 3, "max": 900}),
            ("ig_reels", "ig_reels.max_width", 1920),
            ("ig_reels", "ig_reels.video_bitrate", 25_000_000),
            ("ig_stories", "ig_stories.file_size", 100_000_000),
            ("ig_stories", "ig_stories.duration", {"min": 3, "max": 60}),
            ("tiktok_content_posting_api", "tiktok_api.width_bounds", {"min": 360, "max": 4096}),
            ("tiktok_content_posting_api", "tiktok_api.frame_rate", {"min": 23, "max": 60}),
            ("tiktok_content_posting_api", "tiktok_api.file_size", 4_000_000_000),
            ("tiktok_infeed_auction_nonspark", "tiktok_infeed.video_bitrate", 516_000),
            ("tiktok_topview_reservation", "tiktok_topview.video_bitrate", 2_500_000),
            ("tiktok_topview_reservation", "tiktok_topview.duration", {"min": 5, "max": 60}),
            ("youtube_standard", "youtube.max_file_size", 256_000_000_000),
            ("linkedin_organic", "linkedin_organic.aspect_ratio", {"min": 0.417, "max": 2.4}),
            ("linkedin_organic", "linkedin_organic.frame_rate", {"min": 10, "max": 60}),
            ("linkedin_video_ads", "linkedin_ads.max_file_size", 500_000_000),
            ("linkedin_video_ads", "linkedin_ads.width", {"min": 360, "max": 1920}),
            ("linkedin_video_ads", "linkedin_ads.audio_sample_rate", 64000),
            ("linkedin_ctv", "linkedin_ctv.duration", {"min": 6, "max": 60}),
            ("linkedin_ctv", "linkedin_ctv.video_bitrate", 12_000_000),
            ("linkedin_ctv", "linkedin_ctv.audio_sample_rate", 48000),
        ],
    )
    def test_high_risk_values_match_the_register(
        self, catalog, preset_id: str, rule_id: str, expected: object
    ) -> None:
        preset = catalog.by_id(preset_id)
        assert preset is not None, preset_id
        rule = next((r for r in preset.rules if r.rule_id == rule_id), None)
        assert rule is not None, rule_id
        assert rule.expected == expected

    def test_the_two_instagram_aspect_ratio_bounds_genuinely_differ(self, catalog) -> None:
        """Conflict C-4 — Reels is 0.01:1 and Stories is 0.1:1 in the same document."""
        reels = catalog.by_id("ig_reels")
        stories = catalog.by_id("ig_stories")
        reels_rule = next(r for r in reels.rules if r.rule_id == "ig_reels.aspect_ratio_range")
        stories_rule = next(r for r in stories.rules if r.rule_id == "ig_stories.aspect_ratio_range")
        assert reels_rule.expected["min"] == 0.01
        assert stories_rule.expected["min"] == 0.1
        assert reels_rule.expected["min"] != stories_rule.expected["min"]

    def test_linkedin_uses_decimal_byte_thresholds(self, catalog) -> None:
        """P4-A10 / conflict L-C5 — the conservative reading."""
        ads = catalog.by_id("linkedin_video_ads")
        size_rule = next(r for r in ads.rules if r.rule_id == "linkedin_ads.max_file_size")
        assert size_rule.expected == 500_000_000  # decimal, not 524_288_000
        assert ads.byte_convention and "ecimal" in ads.byte_convention

    def test_linkedin_ads_carry_the_published_aspect_ratio_tolerance(self, catalog) -> None:
        ads = catalog.by_id("linkedin_video_ads")
        rule = next(r for r in ads.rules if r.rule_id == "linkedin_ads.aspect_ratio")
        assert rule.tolerance == 0.05
        assert rule.relative_tolerance is True


class TestPerPresetShape:
    def test_instagram_feed_has_no_failing_rules(self, catalog) -> None:
        """Every Feed value is medium confidence, so none may reject a file."""
        preset = catalog.by_id("ig_feed")
        assert preset.failing_rules() == ()

    def test_youtube_standard_has_exactly_two_failing_rules(self, catalog) -> None:
        """P4-A6 — container list and the 256 GB ceiling, and nothing else."""
        preset = catalog.by_id("youtube_standard")
        assert {r.rule_id for r in preset.failing_rules()} == {
            "youtube.container_supported",
            "youtube.max_file_size",
        }

    def test_youtube_shorts_inherits_no_encoding_failures(self, catalog) -> None:
        """P4-A7 — standard-upload recommendations must not become Shorts requirements."""
        preset = catalog.by_id("youtube_shorts")
        failing = {r.rule_id for r in preset.failing_rules()}
        assert failing == {
            "youtube_shorts.container_supported",
            "youtube_shorts.max_file_size",
        }
        for rule_id in failing:
            assert "codec" not in rule_id
            assert "bitrate" not in rule_id

    def test_the_reels_tab_eligibility_rules_are_eligibility_and_warn(self, catalog) -> None:
        """P4-A5 — a discovery condition must never reject a file."""
        preset = catalog.by_id("ig_reels")
        eligibility = [r for r in preset.rules if r.classification is Classification.ELIGIBILITY]
        assert len(eligibility) == 2
        for rule in eligibility:
            assert rule.severity is Severity.WARN

    def test_ctv_loudness_is_reported_not_judged(self, catalog) -> None:
        preset = catalog.by_id("linkedin_ctv")
        rule = next(r for r in preset.rules if r.rule_id == "linkedin_ctv.loudness")
        assert rule.classification is Classification.UNKNOWN
        assert rule.measurable_offline is False

    def test_documented_gaps_are_marked_unmeasurable(self, presets) -> None:
        """Register gaps G-1, G-2 and G-4 must not claim to be measured."""
        for preset, rule in all_rules(presets):
            if rule.property_path in ("container.edit_lists_present", "video.gop_closed"):
                assert rule.measurable_offline is False or rule.note, (
                    f"{preset.preset_id}:{rule.rule_id} should disclose the measurement gap"
                )


class TestPresetMetadata:
    def test_every_preset_carries_versioning_and_caveats(self, presets) -> None:
        for preset in presets:
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}\.\d+", preset.ruleset_version), preset.preset_id
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", preset.last_verified_date), preset.preset_id
            assert preset.caveats, f"{preset.preset_id} should disclose its limitations"
            assert preset.description.strip()

    def test_every_preset_is_shipped_origin(self, presets) -> None:
        assert all(p.origin == "shipped" for p in presets)

    def test_conflicting_paths_are_surfaced_not_resolved(self, catalog) -> None:
        """P4-A9 — TikTok's four-way duration contradiction must reach the user."""
        api = catalog.by_id("tiktok_content_posting_api")
        info_rules = [r for r in api.rules if r.classification is Classification.UNKNOWN]
        durations = [r for r in info_rules if r.property_path == "file.duration_seconds"]
        assert len(durations) >= 2, "the other paths' documented limits must be reported"
        # The Studio (30 min) and in-app (60 min) figures must both reach the user, so
        # the contradiction is visible rather than silently resolved in our favour.
        assert any(r.expected == 1800 for r in durations), "Studio's 30-minute limit not surfaced"
        assert any(r.expected == 3600 for r in durations), "in-app 60-minute limit not surfaced"
        assert all("Studio" in r.explanation or "in-app" in r.explanation for r in durations)

    def test_linkedin_organic_duration_conflict_is_warn_then_fail(self, catalog) -> None:
        """Conflict L-C2 — warn between 10 and 15 minutes, fail only above 15."""
        preset = catalog.by_id("linkedin_organic")
        hard = next(r for r in preset.rules if r.rule_id == "linkedin_organic.max_duration_hard")
        soft = next(r for r in preset.rules if r.rule_id == "linkedin_organic.max_duration_documented")
        assert hard.severity is Severity.FAIL and hard.expected == 900
        assert soft.severity is Severity.WARN and soft.expected == 600


def test_presets_are_pure_data_with_no_executable_content() -> None:
    """P4-A11 — a preset is data; it must not reference code."""
    for path in sorted(PRESETS_DIR.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        text = path.read_text(encoding="utf-8")
        for token in ("import ", "lambda", "eval(", "exec(", "__"):
            assert token not in text, f"{path.name} contains {token!r}"
