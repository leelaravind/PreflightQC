"""Phase 8 — report contents, self-containment and claim safety (P8-A1..A11)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from factories import build_media, default_media, ffprobe_payload, preset_payload, rule
from preflightqc.reporting import claims, csv_writer, html_renderer
from preflightqc.reporting.export import ExportFormat, default_output_dir, export
from preflightqc.reporting.model import build_report
from preflightqc.results.aggregate import (
    InspectionFailure,
    build_file_result,
    build_not_inspected,
    summarise,
)
from preflightqc.rules.engine import evaluate
from preflightqc.rules.loader import build_preset

STARTED = datetime(2026, 8, 9, 14, 30, 0, tzinfo=UTC)
FINISHED = datetime(2026, 8, 9, 14, 31, 12, tzinfo=UTC)


@pytest.fixture
def preset():
    return build_preset(
        preset_payload(
            rules=[
                rule("t.width", property_path="video.width", operator="lte", expected=1920),
                rule(
                    "t.ratio",
                    property_path="video.display_aspect_ratio",
                    operator="eq",
                    expected=0.5625,
                    tolerance=0.01,
                    classification="RECOMMENDATION",
                    severity="WARN",
                ),
                rule(
                    "t.bitrate",
                    property_path="video.bitrate",
                    operator="lte",
                    expected=25_000_000,
                ),
            ],
            caveats=["This preset is for testing only."],
        )
    )


def make_report(preset, *, cancelled: bool = False, include_failure: bool = True):
    good = default_media()
    wide = build_media(ffprobe=ffprobe_payload(video={"width": 3840, "height": 2160}))

    results = [
        build_file_result(
            path=Path("C:/clips/good.mp4"),
            media=good,
            findings=evaluate(good, preset),
            preset_id=preset.preset_id,
            ruleset_version=preset.ruleset_version,
        ),
        build_file_result(
            path=Path("C:/clips/too_wide.mp4"),
            media=wide,
            findings=evaluate(wide, preset),
            preset_id=preset.preset_id,
            ruleset_version=preset.ruleset_version,
        ),
    ]
    if include_failure:
        results.append(
            build_not_inspected(
                path=Path("C:/clips/corrupt.mp4"),
                failure=InspectionFailure(
                    "MALFORMED_OUTPUT", "the file could not be parsed as media", "It may be corrupt."
                ),
                preset_id=preset.preset_id,
                ruleset_version=preset.ruleset_version,
            )
        )

    summary = summarise(
        tuple(results),
        preset_id=preset.preset_id,
        preset_display_name=preset.display_name,
        ruleset_version=preset.ruleset_version,
        completed=not cancelled,
        cancelled=cancelled,
    )
    return build_report(
        results=results,
        summary=summary,
        preset=preset,
        product_version="0.1.0-dev",
        scan_started=STARTED,
        scan_finished=FINISHED,
        inspector_versions={"ffprobe": "7.1", "mediainfo": "26.05"},
    )


class TestRequiredContents:
    def test_html_contains_every_required_element(self, preset) -> None:
        """P8-A1 / spec 17.2."""
        html = html_renderer.render(make_report(preset))
        for required in (
            "0.1.0-dev",
            "2026-08-09T14:30:00",
            "2026-08-09T14:31:12",
            preset.display_name,
            preset.preset_id,
            preset.ruleset_version,
            preset.last_verified_date,
            "ffprobe",
            "7.1",
            "26.05",
            "good.mp4",
            "too_wide.mp4",
            "corrupt.mp4",
            claims.APPROVED_CLAIM,
            "No source video file was opened for writing",
        ):
            assert required in html, f"missing from report: {required!r}"

    def test_csv_contains_every_required_element(self, preset) -> None:
        report = make_report(preset)
        findings = csv_writer.render_findings(report)
        summary = csv_writer.render_summary(report)
        assert "rule_id" in findings
        assert "too_wide.mp4" in findings
        assert "corrupt.mp4" in findings
        for required in ("0.1.0-dev", preset.ruleset_version, "ffprobe", claims.APPROVED_CLAIM):
            assert required in summary

    def test_findings_show_detected_expected_and_source(self, preset) -> None:
        csv_text = csv_writer.render_findings(make_report(preset))
        assert "3840 px" in csv_text
        assert "required: at most 1920 px" in csv_text
        assert "https://example.invalid/spec" in csv_text
        assert "2026-08-09" in csv_text

    def test_a_not_inspected_file_still_appears(self, preset) -> None:
        """A file that vanished from the report is a file the user will ship broken."""
        csv_text = csv_writer.render_findings(make_report(preset))
        assert "corrupt.mp4" in csv_text
        assert "NOT_INSPECTED" in csv_text


class TestSelfContainment:
    def test_the_html_report_makes_no_external_requests(self, preset) -> None:
        """P8-A2 / spec 17.3 — a report must not phone anywhere when opened."""
        html = html_renderer.render(make_report(preset))
        assert html_renderer.find_external_references(html) == ()

    def test_source_urls_appear_as_text_not_as_links(self, preset) -> None:
        html = html_renderer.render(make_report(preset))
        assert "https://example.invalid/spec" in html
        assert 'href="https://example.invalid/spec"' not in html

    def test_no_script_tags_are_emitted(self, preset) -> None:
        html = html_renderer.render(make_report(preset))
        assert "<script" not in html.lower()


class TestClaimSafety:
    def test_no_forbidden_claim_appears(self, preset) -> None:
        """P8-A4 / spec AC-11."""
        report = make_report(preset)
        for text in (
            html_renderer.render(report),
            csv_writer.render_findings(report),
            csv_writer.render_summary(report),
        ):
            assert claims.contains_forbidden_claim(text) == ()

    def test_the_approved_claim_is_present(self, preset) -> None:
        html = html_renderer.render(make_report(preset))
        assert claims.APPROVED_CLAIM in html

    @pytest.mark.parametrize("phrase", claims.FORBIDDEN_CLAIMS)
    def test_the_detector_catches_each_forbidden_phrase(self, phrase: str) -> None:
        assert claims.contains_forbidden_claim(f"This file is {phrase} by the platform.")

    @pytest.mark.parametrize("phrase", claims.FORBIDDEN_CLAIMS)
    def test_a_negated_phrase_is_the_disclaimer_not_the_claim(self, phrase: str) -> None:
        """The required disclaimer contains the forbidden words.

        The EULA has to say the software is *not* certified by any platform. A scanner
        that cannot tell an assertion from its negation flags that sentence, and the
        obvious way to make it pass is to delete the disclaimer — which is the opposite
        of what the specification requires.
        """
        assert claims.contains_forbidden_claim(f"This software is not {phrase} any platform.") == ()

    def test_the_real_eula_disclaimer_passes(self) -> None:
        text = (
            "A PASS result is not a guarantee of acceptance, and the Software is not\n"
            "affiliated with, endorsed by, or certified by any platform whose "
            "specifications\nit validates against."
        )
        assert claims.contains_forbidden_claim(text) == ()

    def test_a_negation_in_the_previous_sentence_does_not_launder_a_claim(self) -> None:
        """Negation only counts inside the same sentence, or the guard is useless."""
        text = "This tool is not a toy. Your file is guaranteed accepted by the platform."
        assert claims.contains_forbidden_claim(text) == ("guaranteed accepted",)

    def test_a_distant_negation_does_not_launder_a_claim(self) -> None:
        text = (
            "PreflightQC does not do many things, and here is a very long sentence "
            "written purely to put distance between that word and what follows, which "
            "is that your upload will be accepted"
        )
        assert claims.contains_forbidden_claim(text) == ("will be accepted",)


class TestEscaping:
    def test_a_hostile_filename_is_escaped(self, preset) -> None:
        """Filenames are attacker-influenced text in a document users email onward."""
        media = default_media()
        result = build_file_result(
            path=Path('C:/clips/<script>alert(1)</script>.mp4'),
            media=media,
            findings=evaluate(media, preset),
            preset_id=preset.preset_id,
            ruleset_version=preset.ruleset_version,
        )
        summary = summarise(
            (result,),
            preset_id=preset.preset_id,
            preset_display_name=preset.display_name,
            ruleset_version=preset.ruleset_version,
        )
        html = html_renderer.render(
            build_report(
                results=[result],
                summary=summary,
                preset=preset,
                product_version="0.1.0-dev",
                scan_started=STARTED,
                scan_finished=FINISHED,
                inspector_versions={},
            )
        )
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html


class TestPartialBatches:
    def test_a_cancelled_batch_is_marked_partial(self, preset) -> None:
        """P8-A6."""
        report = make_report(preset, cancelled=True)
        assert report.is_partial
        assert "PARTIAL" in report.partial_note
        html = html_renderer.render(report)
        assert "Partial report" in html


class TestCrossFormatConsistency:
    def test_csv_and_html_agree_on_every_status(self, preset) -> None:
        """P8-A8 — one shared model means they cannot drift."""
        report = make_report(preset)
        html = html_renderer.render(report)
        summary_csv = csv_writer.render_summary(report)
        for status, count in report.status_counts.items():
            if count:
                assert f"Files {status},{count}" in summary_csv
                assert str(count) in html

    def test_finding_counts_match_between_formats(self, preset) -> None:
        report = make_report(preset)
        csv_rows = csv_writer.render_findings(report).strip().splitlines()
        # Every file contributes at least one row, so the CSV is a complete record.
        expected = sum(max(1, len(f.actionable)) for f in report.files)
        assert len(csv_rows) - 1 == expected


class TestCsvFormat:
    def test_encoding_is_utf8_with_a_bom(self, preset) -> None:
        """P8-A5 — without the BOM, Excel mangles every non-ASCII filename."""
        payload = csv_writer.encode(csv_writer.render_findings(make_report(preset)))
        assert payload.startswith(b"\xef\xbb\xbf")

    def test_line_endings_are_crlf(self, preset) -> None:
        assert "\r\n" in csv_writer.render_findings(make_report(preset))

    def test_column_order_is_stable(self, preset) -> None:
        header = csv_writer.render_findings(make_report(preset)).splitlines()[0]
        assert header.split(",")[:4] == ["file_name", "file_path", "file_status", "severity"]

    def test_embedded_commas_and_quotes_are_quoted(self, preset) -> None:
        media = default_media()
        result = build_file_result(
            path=Path('C:/clips/a,b "c".mp4'),
            media=media,
            findings=evaluate(media, preset),
            preset_id=preset.preset_id,
            ruleset_version=preset.ruleset_version,
        )
        summary = summarise(
            (result,),
            preset_id=preset.preset_id,
            preset_display_name=preset.display_name,
            ruleset_version=preset.ruleset_version,
        )
        csv_text = csv_writer.render_findings(
            build_report(
                results=[result],
                summary=summary,
                preset=preset,
                product_version="0.1.0-dev",
                scan_started=STARTED,
                scan_finished=FINISHED,
                inspector_versions={},
            )
        )
        assert '"a,b ""c"".mp4"' in csv_text


class TestExport:
    def test_both_formats_write_successfully(self, preset, tmp_path: Path) -> None:
        report = make_report(preset)
        html_result = export(report, tmp_path / "r.html", ExportFormat.HTML)
        csv_result = export(report, tmp_path / "r.csv", ExportFormat.CSV)
        assert html_result.ok and csv_result.ok
        assert (tmp_path / "r.html").is_file()
        assert (tmp_path / "r.csv").is_file()
        assert (tmp_path / "r_summary.csv").is_file()

    def test_a_write_failure_is_actionable_and_loses_nothing(self, preset, tmp_path: Path) -> None:
        """P8-A7 — results stay in memory; the user can retry elsewhere."""
        blocked = tmp_path / "nope"
        blocked.mkdir()
        result = export(make_report(preset), blocked, ExportFormat.HTML)
        assert not result.ok
        assert result.error
        assert "still loaded" in result.hint

    def test_the_default_output_dir_is_not_a_source_folder(self) -> None:
        """P8-A10 — never write a report beside a client's masters."""
        default = str(default_output_dir()).lower()
        assert "preflightqc" in default
        assert default.endswith("reports")

    def test_suggested_filenames_are_path_safe(self, preset) -> None:
        name = export.__module__ and __import__(
            "preflightqc.reporting.export", fromlist=["suggested_filename"]
        ).suggested_filename(make_report(preset), ExportFormat.CSV)
        assert ":" not in name
        assert name.endswith(".csv")


class TestDeterminism:
    def test_the_same_batch_renders_identically(self, preset) -> None:
        """P8-A9 — with the clock injected, reports are byte-stable."""
        first = html_renderer.render(make_report(preset))
        second = html_renderer.render(make_report(preset))
        assert first == second

    def test_custom_profiles_never_print_a_platform_name(self) -> None:
        """Spec 16.5."""
        from preflightqc.profiles.compiler import compile_profile
        from preflightqc.profiles.model import CustomProfile, ProfileProperty, PropertySpec

        profile = CustomProfile(
            profile_id="custom_abc123456789",
            name="Acme Q3 Delivery",
            properties={ProfileProperty.WIDTH: PropertySpec(maximum=1920)},
        )
        compiled = compile_profile(profile)
        media = default_media()
        result = build_file_result(
            path=Path("C:/clips/a.mp4"),
            media=media,
            findings=evaluate(media, compiled),
            preset_id=compiled.preset_id,
            ruleset_version=compiled.ruleset_version,
        )
        report = build_report(
            results=[result],
            summary=summarise(
                (result,),
                preset_id=compiled.preset_id,
                preset_display_name=compiled.display_name,
                ruleset_version=compiled.ruleset_version,
            ),
            preset=compiled,
            product_version="0.1.0-dev",
            scan_started=STARTED,
            scan_finished=FINISHED,
            inspector_versions={},
        )
        html = html_renderer.render(report)
        assert "Acme Q3 Delivery" in html
        assert report.preset_platform == "Custom profile"
        for platform in ("Instagram", "TikTok", "YouTube", "LinkedIn"):
            assert platform not in html
