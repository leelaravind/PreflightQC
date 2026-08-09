"""Phase 3 — overall status and batch summary (P3-A9, P3-A10).

The exhaustive truth table for specification 7.2 lives here.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import pytest

from factories import default_media
from preflightqc.results.aggregate import (
    DECIDING_SEVERITIES,
    BatchSummary,
    FileStatus,
    InspectionFailure,
    build_file_result,
    build_not_inspected,
    deciding_severities,
    overall_status,
    summarise,
)
from preflightqc.rules.finding import Finding, SourceReference
from preflightqc.rules.severity import Classification, Severity

SOURCE = SourceReference("S1", "Test", "https://example.invalid", "2026-08-09", "HIGH")


def finding(severity: Severity, *, rule_id: str = "r", passed: bool = False) -> Finding:
    return Finding(
        rule_id=rule_id,
        severity=severity,
        classification=Classification.HARD_REQUIREMENT,
        property_path="video.width",
        property_label="Width",
        detected="1080 px",
        expected="required: at most 1920 px",
        explanation="test",
        source=SOURCE,
        passed=passed,
    )


class TestOverallStatusTruthTable:
    @pytest.mark.parametrize(
        ("has_fail", "has_warn", "has_other"),
        list(itertools.product([False, True], repeat=3)),
    )
    def test_every_combination(self, has_fail: bool, has_warn: bool, has_other: bool) -> None:
        """P3-A9 — all eight combinations of {FAIL, WARN, other}."""
        findings: list[Finding] = []
        if has_fail:
            findings.append(finding(Severity.FAIL, rule_id="f"))
        if has_warn:
            findings.append(finding(Severity.WARN, rule_id="w"))
        if has_other:
            findings.append(finding(Severity.INFO, rule_id="i"))
            findings.append(finding(Severity.UNKNOWN, rule_id="u"))

        status = overall_status(deciding_severities(tuple(findings)))
        if has_fail:
            assert status is FileStatus.FAIL
        elif has_warn:
            assert status is FileStatus.WARN
        else:
            assert status is FileStatus.PASS

    def test_info_only_is_pass(self) -> None:
        """P3-A10."""
        findings = (finding(Severity.INFO, rule_id="a"), finding(Severity.INFO, rule_id="b"))
        assert overall_status(deciding_severities(findings)) is FileStatus.PASS

    def test_unknown_only_is_pass(self) -> None:
        """P3-A10 — 'we could not determine this' must never read as 'your file is wrong'."""
        findings = (finding(Severity.UNKNOWN, rule_id="a"), finding(Severity.UNKNOWN, rule_id="b"))
        assert overall_status(deciding_severities(findings)) is FileStatus.PASS

    def test_many_unknowns_alongside_one_warn_is_warn_not_fail(self) -> None:
        findings = (
            *(finding(Severity.UNKNOWN, rule_id=f"u{i}") for i in range(20)),
            finding(Severity.WARN, rule_id="w"),
        )
        assert overall_status(deciding_severities(findings)) is FileStatus.WARN

    def test_no_findings_at_all_is_pass(self) -> None:
        assert overall_status(()) is FileStatus.PASS

    def test_passing_findings_never_decide_status(self) -> None:
        """A satisfied rule is evidence of conformance, not of failure."""
        findings = (finding(Severity.INFO, rule_id="p", passed=True),)
        assert overall_status(deciding_severities(findings)) is FileStatus.PASS


class TestStructuralExclusion:
    def test_deciding_severities_are_exactly_fail_and_warn(self) -> None:
        assert set(DECIDING_SEVERITIES) == {Severity.FAIL, Severity.WARN}

    def test_passing_info_or_unknown_into_overall_status_raises(self) -> None:
        """Structural exclusion: these cannot reach the decision by accident."""
        for severity in (Severity.INFO, Severity.UNKNOWN):
            with pytest.raises(ValueError, match="must not participate"):
                overall_status((severity,))

    def test_deciding_severities_filters_out_info_and_unknown(self) -> None:
        findings = (
            finding(Severity.FAIL, rule_id="a"),
            finding(Severity.INFO, rule_id="b"),
            finding(Severity.UNKNOWN, rule_id="c"),
            finding(Severity.WARN, rule_id="d"),
        )
        assert set(deciding_severities(findings)) == {Severity.FAIL, Severity.WARN}


class TestFileResult:
    def test_counts_exclude_passing_findings(self) -> None:
        result = build_file_result(
            path=Path("a.mp4"),
            media=default_media(),
            findings=(
                finding(Severity.WARN, rule_id="w"),
                finding(Severity.INFO, rule_id="p1", passed=True),
                finding(Severity.INFO, rule_id="p2", passed=True),
            ),
            preset_id="test",
            ruleset_version="1",
        )
        assert result.counts[Severity.WARN] == 1
        assert result.counts[Severity.INFO] == 0
        assert result.checks_passed == 2

    def test_not_inspected_is_not_fail(self) -> None:
        """Spec 7.4 — PreflightQC did not validate this file, so it has no verdict."""
        result = build_not_inspected(
            path=Path("broken.mp4"),
            failure=InspectionFailure("FILE_UNREADABLE", "could not read the file"),
            preset_id="test",
            ruleset_version="1",
        )
        assert result.status is FileStatus.NOT_INSPECTED
        assert result.status is not FileStatus.FAIL
        assert not result.was_inspected
        assert result.findings == ()


class TestBatchSummary:
    def _summary(self, statuses: list[FileStatus]) -> BatchSummary:
        results = tuple(
            build_not_inspected(
                path=Path(f"{i}.mp4"),
                failure=InspectionFailure("X", "y"),
                preset_id="p",
                ruleset_version="1",
            )
            if status is FileStatus.NOT_INSPECTED
            else build_file_result(
                path=Path(f"{i}.mp4"),
                media=default_media(),
                findings=(finding(Severity.FAIL),) if status is FileStatus.FAIL
                else (finding(Severity.WARN),) if status is FileStatus.WARN
                else (),
                preset_id="p",
                ruleset_version="1",
            )
            for i, status in enumerate(statuses)
        )
        return summarise(
            results, preset_id="p", preset_display_name="P", ruleset_version="1"
        )

    def test_not_inspected_is_counted_separately_from_fail(self) -> None:
        """Spec 14.2 — the count a user acts on must not be inflated."""
        summary = self._summary(
            [FileStatus.PASS, FileStatus.FAIL, FileStatus.NOT_INSPECTED, FileStatus.NOT_INSPECTED]
        )
        assert summary.failed == 1
        assert summary.not_inspected == 2
        assert summary.passed == 1

    def test_counts_cover_every_status(self) -> None:
        summary = self._summary([FileStatus.PASS, FileStatus.WARN, FileStatus.FAIL])
        assert set(summary.status_counts) == set(FileStatus)
        assert summary.inspected == 3

    def test_a_cancelled_batch_is_partial(self) -> None:
        summary = summarise(
            (), preset_id="p", preset_display_name="P", ruleset_version="1", cancelled=True
        )
        assert summary.is_partial

    def test_a_completed_batch_is_not_partial(self) -> None:
        summary = summarise((), preset_id="p", preset_display_name="P", ruleset_version="1")
        assert not summary.is_partial
