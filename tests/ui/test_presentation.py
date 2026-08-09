"""Presentation logic, tested without a window.

Every finding in `docs/design/UI-AUDIT-V1.md` was invisible to a 1,114-test suite because
nothing imported `preflightqc.ui`. The most serious of them — a zero-byte file reporting
PASS — is exactly the kind of defect a test can hold down forever once it exists.

These tests need no Qt display: the view models and the design tokens are deliberately
Qt-free, so the decisions worth testing can be tested directly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from preflightqc.results.aggregate import FileStatus
from preflightqc.ui import design, severity_style, viewmodels


class TestValueHumanising:
    """The engine's strings are correct and machine-shaped. These are what a user reads."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (0.5625, "9:16 (0.5625)"),
            (16 / 9, "16:9 (1.77778)"),
            (0.8, "4:5 (0.8)"),
            (1.0, "1:1 (1)"),
        ],
    )
    def test_recognised_aspect_ratios_get_their_name(self, value: float, expected: str) -> None:
        assert viewmodels.format_ratio(value) == expected

    def test_a_ratio_nobody_names_keeps_its_decimal(self) -> None:
        assert viewmodels.format_ratio(1.234567) == "1.23457"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (0, "0 bytes"),
            (43, "43 bytes"),
            (999, "999 bytes"),
            (1000, "1.0 KB (1,000 bytes)"),
            (104857600, "104.9 MB (104,857,600 bytes)"),
        ],
    )
    def test_byte_counts_are_readable_without_losing_the_exact_number(
        self, value: int, expected: str
    ) -> None:
        """Size limits are expressed in exact bytes, so both forms have to survive."""
        assert viewmodels.format_bytes(value) == expected

    @pytest.mark.parametrize(
        ("text", "path", "expected"),
        [
            ("False", "container.fast_start", "not enabled"),
            ("True", "container.fast_start", "enabled"),
            ("True", "audio.present", "present"),
            ("False", "", "no"),
            ("True", "", "yes"),
        ],
    )
    def test_booleans_are_phrased_for_the_property(
        self, text: str, path: str, expected: str
    ) -> None:
        assert viewmodels.humanise_value(text, path) == expected

    def test_a_value_with_no_rule_passes_through_untouched(self) -> None:
        assert viewmodels.humanise_value("h264", "video.codec") == "h264"

    @pytest.mark.parametrize(
        ("text", "label", "value"),
        [
            ("required: True", "Required", "True"),
            ("recommended: 0.5625", "Recommended", "0.5625"),
            ("for eligibility: between 5 and 90 s", "For eligibility", "between 5 and 90 s"),
            ("anything else", "Expected", "anything else"),
        ],
    )
    def test_the_expectation_qualifier_becomes_a_label(
        self, text: str, label: str, value: str
    ) -> None:
        """`Expected: required: True` was a double colon and a machine value."""
        assert viewmodels.split_expectation(text) == (label, value)


class TestPresetLabels:
    """Audit F-9: nine of twelve presets said their platform twice."""

    def _option(self, platform: str, name: str) -> viewmodels.PresetOption:
        return viewmodels.PresetOption(
            preset_id="x",
            display_name=name,
            platform=platform,
            ruleset_version="1",
            last_verified="2026-08-09",
            caveats=(),
            is_custom=False,
        )

    @pytest.mark.parametrize(
        ("platform", "name", "expected"),
        [
            ("LinkedIn", "LinkedIn — Connected TV (CTV) Ads", "LinkedIn — Connected TV (CTV) Ads"),
            ("TikTok", "TikTok — Studio / web upload", "TikTok — Studio / web upload"),
            ("YouTube", "YouTube — Shorts", "YouTube — Shorts"),
            ("Meta / Instagram", "Instagram Reels", "Meta / Instagram — Instagram Reels"),
        ],
    )
    def test_the_platform_is_never_repeated(
        self, platform: str, name: str, expected: str
    ) -> None:
        assert self._option(platform, name).menu_label == expected

    def test_a_preset_named_only_after_its_platform_still_has_a_label(self) -> None:
        assert self._option("TikTok", "TikTok").menu_label == "TikTok"

    def test_the_context_line_carries_the_verification_date(self) -> None:
        """The date a source was last checked is a trust signal, not a status message."""
        option = viewmodels.PresetOption(
            preset_id="x",
            display_name="Reels",
            platform="Meta",
            ruleset_version="2026-08-09.1",
            last_verified="2026-08-09",
            caveats=(),
            is_custom=False,
            rule_count=22,
        )
        assert "2026-08-09" in option.context_line
        assert "22 rules" in option.context_line


class TestTheInconclusiveQualifier:
    """Audit F-1, the finding that changes what a user believes about their file."""

    def _row(self, **kwargs) -> viewmodels.FileRow:
        defaults = {
            "index": 0,
            "name": "clip.mp4",
            "path": "C:/clip.mp4",
            "status": "PASS",
            "fail_count": 0,
            "warn_count": 0,
            "unknown_count": 21,
            "checks_passed": 1,
            "failure_message": "",
            "failure_hint": "",
            "is_complete": True,
            "is_inconclusive": True,
        }
        defaults.update(kwargs)
        return viewmodels.FileRow(**defaults)  # type: ignore[arg-type]

    def test_a_vacuous_pass_is_not_shown_as_pass(self) -> None:
        assert self._row().display_status == "INCONCLUSIVE"

    def test_the_canonical_status_is_untouched(self) -> None:
        """Severity semantics do not change; only what the interface says changes."""
        assert self._row().status == "PASS"

    def test_a_real_pass_is_still_a_pass(self) -> None:
        row = self._row(is_inconclusive=False, unknown_count=0, checks_passed=21)
        assert row.display_status == "PASS"
        assert row.summary_text == "21 checks passed"

    def test_the_summary_says_nothing_was_determined(self) -> None:
        assert self._row().summary_text == "Nothing determined — 21 unknown"

    def test_the_reason_is_stated_in_one_sentence(self) -> None:
        assert "no video stream" in viewmodels.FileRow.INCONCLUSIVE_REASON.lower()

    def test_a_failure_message_is_capitalised_for_a_column(self) -> None:
        row = self._row(failure_message="the file is no longer available")
        assert row.summary_text == "The file is no longer available"

    def test_a_queued_row_says_so(self) -> None:
        assert self._row(is_complete=False).summary_text == "Queued"


class TestTheReadoutAgreesWithTheTable:
    """One screen must not give two accounts of the same batch."""

    def _row(self, status: str, *, inconclusive: bool = False) -> viewmodels.FileRow:
        return viewmodels.FileRow(
            index=0,
            name="c.mp4",
            path="c.mp4",
            status=status,
            fail_count=0,
            warn_count=0,
            unknown_count=0,
            checks_passed=1,
            failure_message="",
            failure_hint="",
            is_complete=True,
            is_inconclusive=inconclusive,
        )

    def test_counts_follow_what_the_rows_display(self) -> None:
        rows = [
            self._row("FAIL"),
            self._row("PASS", inconclusive=True),
            self._row("PASS"),
        ]
        segments = dict(viewmodels.build_readout_segments(rows))
        assert segments["FAIL"] == 1
        assert segments["INCONCLUSIVE"] == 1
        assert segments["PASS"] == 1

    def test_incomplete_rows_are_not_counted(self) -> None:
        """A queued file has no outcome, so it must not inflate any bucket."""
        pending = viewmodels.build_file_row(1, Path("queued.mp4"), None)
        segments = dict(viewmodels.build_readout_segments([self._row("PASS"), pending]))
        assert sum(segments.values()) == 1

    def test_the_order_never_changes(self) -> None:
        """A readout you have to re-read every time is not a readout."""
        empty = viewmodels.build_readout_segments([])
        assert [name for name, _ in empty] == list(viewmodels.READOUT_ORDER)
        assert viewmodels.READOUT_ORDER[0] == FileStatus.FAIL.value
        assert viewmodels.READOUT_ORDER.index("INCONCLUSIVE") < viewmodels.READOUT_ORDER.index(
            FileStatus.PASS.value
        )


class TestSeverityPresentation:
    def test_every_tone_carries_a_marker_and_a_label(self) -> None:
        """Colour is reinforcement. The marker and the label are the guarantee."""
        for tone in design.DISTINCT_TONES:
            assert tone.marker.strip()
            assert tone.label.strip()

    def test_markers_are_unique(self) -> None:
        markers = [tone.marker for tone in design.DISTINCT_TONES]
        assert len(set(markers)) == len(markers)

    def test_labels_are_unique(self) -> None:
        labels = [tone.label for tone in design.DISTINCT_TONES]
        assert len(set(labels)) == len(labels)

    def test_a_recommendation_never_borrows_the_failure_treatment(self) -> None:
        """Plan §8: a recommendation must never visually imply a hard failure."""
        assert design.WARN_TONE.foreground != design.FAIL_TONE.foreground
        assert design.WARN_TONE.marker != design.FAIL_TONE.marker
        assert design.WARN_TONE.label != design.FAIL_TONE.label

    def test_inconclusive_uses_the_unknown_family_not_the_pass_family(self) -> None:
        assert design.INCONCLUSIVE_TONE.foreground == design.UNKNOWN_TONE.foreground
        assert design.INCONCLUSIVE_TONE.foreground != design.PASS_TONE.foreground

    def test_every_file_status_resolves_to_a_tone(self) -> None:
        for status in FileStatus:
            assert severity_style.for_status(status.value).label

    @pytest.mark.parametrize("severity", ["FAIL", "WARN", "INFO", "UNKNOWN"])
    def test_every_severity_resolves_to_a_tone(self, severity: str) -> None:
        assert severity_style.for_severity(severity).label

    def test_an_unrecognised_name_falls_back_rather_than_raising(self) -> None:
        assert severity_style.for_status("SOMETHING_NEW").label


class TestContrast:
    """The palette's readability is computed, never asserted by eye."""

    @pytest.mark.parametrize(
        ("foreground", "background", "minimum", "description"), design.REQUIRED_CONTRAST
    )
    def test_every_required_pair_meets_its_threshold(
        self, foreground: str, background: str, minimum: float, description: str
    ) -> None:
        ratio = design.contrast_ratio(foreground, background)
        assert ratio >= minimum, f"{description}: {ratio:.2f} < {minimum}"

    def test_the_ratio_maths_is_right(self) -> None:
        assert design.contrast_ratio("#ffffff", "#000000") == pytest.approx(21.0, abs=0.01)
        assert design.contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1.0, abs=0.01)

    def test_a_malformed_colour_raises(self) -> None:
        with pytest.raises(ValueError, match="rrggbb"):
            design.relative_luminance("#fff")


class TestDesignTokenDiscipline:
    """Tokens exist so the interface has one place to change. That has to be enforced."""

    UI_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "preflightqc" / "ui"

    def test_no_hex_colour_outside_the_token_module(self) -> None:
        import re

        pattern = re.compile(r"#[0-9a-fA-F]{6}\b")
        offenders: list[str] = []
        for path in sorted(self.UI_DIR.glob("*.py")):
            if path.name == "design.py":
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line):
                    offenders.append(f"{path.name}:{number}: {line.strip()}")
        assert offenders == [], "hex colours belong in design.py:\n" + "\n".join(offenders)

    def test_the_spacing_scale_is_the_only_scale(self) -> None:
        named = (
            design.SPACE_XXS,
            design.SPACE_XS,
            design.SPACE_SM,
            design.SPACE_MD,
            design.SPACE_LG,
            design.SPACE_XL,
            design.SPACE_2XL,
        )
        assert all(value in design.SPACE for value in named)

    def test_no_typeface_is_bundled(self) -> None:
        """Shipping a font would add a licence obligation to a product gated on licensing."""
        repo = Path(__file__).resolve().parent.parent.parent
        fonts = [
            p
            for p in repo.rglob("*")
            if p.suffix.lower() in {".ttf", ".otf", ".woff", ".woff2"}
            and "third-party" not in p.parts
            and ".venv" not in p.parts
            and "dist" not in p.parts
            and "build" not in p.parts
        ]
        assert fonts == []

    def test_the_minimum_window_is_smaller_than_the_default(self) -> None:
        assert design.MIN_WINDOW_WIDTH < design.DEFAULT_WINDOW_WIDTH
        assert design.MIN_WINDOW_HEIGHT < design.DEFAULT_WINDOW_HEIGHT
