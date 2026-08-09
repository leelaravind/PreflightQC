"""Phase 5 / Phase 10 — batch isolation, cancellation, ordering and the failure matrix.

Claim C4 from the test strategy: **one broken file never terminates a batch, and source
files are never modified.**

Inspectors are simulated at the adapter boundary so every row of specification 23 can be
reached deterministically, including the ones a real inspector would only produce for a
genuinely corrupt or hostile file.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from factories import ffprobe_payload, mediainfo_payload, preset_payload, rule
from preflightqc.adapters import ffprobe as ffprobe_adapter
from preflightqc.adapters import mediainfo as mediainfo_adapter
from preflightqc.adapters.base import FailureKind, InspectorFailure, InspectorSuccess
from preflightqc.orchestration.runner import (
    BatchRunner,
    CancellationToken,
    InspectionCache,
    InspectionSettings,
)
from preflightqc.platform.binaries import InspectorInfo, InspectorKind, StartupReport
from preflightqc.results.aggregate import FileStatus
from preflightqc.rules.loader import build_preset

STARTUP = StartupReport(
    inspectors=(
        InspectorInfo(InspectorKind.FFPROBE, Path("C:/bin/ffprobe.exe"), "7.1", True),
        InspectorInfo(InspectorKind.MEDIAINFO, Path("C:/bin/mediainfo.exe"), "26.05", True),
    )
)


@pytest.fixture
def preset():
    return build_preset(
        preset_payload(
            rules=[rule("t.width", property_path="video.width", operator="lte", expected=1920)]
        )
    )


@pytest.fixture
def media_files(tmp_path: Path) -> list[Path]:
    files = []
    for i in range(5):
        path = tmp_path / f"clip_{i}.mp4"
        path.write_bytes(b"\x00" * 1024)
        files.append(path)
    return files


def install_inspectors(monkeypatch, *, ffprobe_for=None, mediainfo_for=None) -> None:
    """Replace both adapters with per-file scripted behaviour."""

    def default_ff(path: Path):
        return InspectorSuccess(raw=ffprobe_payload(video={}, audio={}))

    def default_mi(path: Path):
        return InspectorSuccess(raw=mediainfo_payload(video={}, audio={}))

    ff = ffprobe_for or default_ff
    mi = mediainfo_for or default_mi

    monkeypatch.setattr(
        ffprobe_adapter, "inspect", lambda binary, path, **kw: ff(path)
    )
    monkeypatch.setattr(
        mediainfo_adapter, "inspect", lambda binary, path, **kw: mi(path)
    )


class TestHappyPath:
    def test_a_clean_batch_produces_a_result_per_file(
        self, monkeypatch, preset, media_files
    ) -> None:
        install_inspectors(monkeypatch)
        outcome = BatchRunner(startup=STARTUP).run(media_files, preset)
        assert len(outcome.results) == len(media_files)
        assert all(r.status is FileStatus.PASS for r in outcome.results)
        assert outcome.summary.passed == len(media_files)
        assert not outcome.partial

    def test_an_empty_batch_is_not_an_error(self, preset) -> None:
        outcome = BatchRunner(startup=STARTUP).run([], preset)
        assert outcome.results == ()
        assert outcome.summary.total_files == 0


class TestIsolation:
    def test_one_unreadable_file_does_not_stop_the_batch(
        self, monkeypatch, preset, media_files
    ) -> None:
        """P5-A1 / spec 23 — the defining property of a batch tool."""
        bad = media_files[2]

        def ff(path: Path):
            if path == bad:
                return InspectorFailure(FailureKind.FILE_UNREADABLE, "cannot read")
            return InspectorSuccess(raw=ffprobe_payload(video={}, audio={}))

        install_inspectors(
            monkeypatch,
            ffprobe_for=ff,
            mediainfo_for=lambda p: (
                InspectorFailure(FailureKind.FILE_UNREADABLE, "cannot read")
                if p == bad
                else InspectorSuccess(raw=mediainfo_payload(video={}, audio={}))
            ),
        )

        outcome = BatchRunner(startup=STARTUP).run(media_files, preset)
        assert len(outcome.results) == len(media_files)
        broken = next(r for r in outcome.results if r.path == bad)
        assert broken.status is FileStatus.NOT_INSPECTED
        assert broken.status is not FileStatus.FAIL
        assert sum(1 for r in outcome.results if r.status is FileStatus.PASS) == 4

    @pytest.mark.parametrize(
        ("kind", "expected_hint_fragment"),
        [
            (FailureKind.PERMISSION_DENIED, "account can read"),
            (FailureKind.FILE_UNREADABLE, "moved, renamed or deleted"),
            (FailureKind.TIMEOUT, "longer timeout"),
            (FailureKind.MALFORMED_OUTPUT, "corrupt or truncated"),
        ],
    )
    def test_every_failure_kind_yields_an_actionable_reason(
        self, monkeypatch, preset, media_files, kind, expected_hint_fragment
    ) -> None:
        """P5-A2 — a reason the user can act on, and never a FAIL."""
        fail = lambda p: InspectorFailure(kind, "simulated")  # noqa: E731
        install_inspectors(monkeypatch, ffprobe_for=fail, mediainfo_for=fail)

        outcome = BatchRunner(startup=STARTUP).run(media_files[:1], preset)
        result = outcome.results[0]
        assert result.status is FileStatus.NOT_INSPECTED
        assert result.failure is not None
        assert result.failure.kind == kind.value
        assert result.failure.hint and expected_hint_fragment in result.failure.hint

    def test_an_internal_error_is_contained_to_one_file(
        self, monkeypatch, preset, media_files
    ) -> None:
        """The isolation boundary must catch defects in our own code too."""
        bad = media_files[1]

        def ff(path: Path):
            if path == bad:
                raise RuntimeError("simulated defect")
            return InspectorSuccess(raw=ffprobe_payload(video={}, audio={}))

        install_inspectors(monkeypatch, ffprobe_for=ff)
        outcome = BatchRunner(startup=STARTUP).run(media_files, preset)
        assert len(outcome.results) == len(media_files)
        broken = next(r for r in outcome.results if r.path == bad)
        assert broken.status is FileStatus.NOT_INSPECTED
        assert broken.failure.kind == "INTERNAL_ERROR"

    def test_a_file_deleted_mid_scan_is_reported_not_fatal(
        self, monkeypatch, preset, tmp_path
    ) -> None:
        vanished = tmp_path / "gone.mp4"
        install_inspectors(monkeypatch)
        outcome = BatchRunner(startup=STARTUP).run([vanished], preset)
        assert outcome.results[0].status is FileStatus.NOT_INSPECTED
        assert "no longer available" in outcome.results[0].failure.message

    def test_one_inspector_failing_still_produces_a_verdict(
        self, monkeypatch, preset, media_files
    ) -> None:
        """Spec 23 — a MediaInfo crash degrades detail, it does not stop validation."""
        install_inspectors(
            monkeypatch,
            mediainfo_for=lambda p: InspectorFailure(FailureKind.CRASHED, "boom"),
        )
        outcome = BatchRunner(startup=STARTUP).run(media_files[:1], preset)
        result = outcome.results[0]
        assert result.status is FileStatus.PASS
        assert any(not r.ok for r in result.diagnostics.inspectors)


class TestOrdering:
    @pytest.mark.parametrize("workers", [1, 2, 4, 8])
    def test_presentation_order_is_input_order(
        self, monkeypatch, preset, media_files, workers: int
    ) -> None:
        """P5-A5 — the list must not reshuffle as results arrive."""
        install_inspectors(monkeypatch)
        outcome = BatchRunner(
            startup=STARTUP, settings=InspectionSettings(workers=workers)
        ).run(media_files, preset)
        assert [r.path for r in outcome.results] == media_files

    def test_results_are_identical_across_worker_counts(
        self, monkeypatch, preset, media_files
    ) -> None:
        install_inspectors(monkeypatch)
        runs = []
        for workers in (1, 4):
            outcome = BatchRunner(
                startup=STARTUP, settings=InspectionSettings(workers=workers)
            ).run(media_files, preset)
            runs.append([(r.path, r.status, len(r.findings)) for r in outcome.results])
        assert runs[0] == runs[1]


class TestCancellation:
    def test_cancelling_preserves_completed_results_and_marks_partial(
        self, monkeypatch, preset, media_files
    ) -> None:
        """P5-A4 / spec 13.6."""
        token = CancellationToken()
        seen = threading.Event()

        def ff(path: Path):
            seen.set()
            return InspectorSuccess(raw=ffprobe_payload(video={}, audio={}))

        install_inspectors(monkeypatch, ffprobe_for=ff)
        token.cancel()  # cancelled before any work starts

        outcome = BatchRunner(startup=STARTUP).run(media_files, preset, token=token)
        assert outcome.cancelled
        assert outcome.partial
        assert outcome.summary.is_partial
        assert all(r.status is FileStatus.NOT_INSPECTED for r in outcome.results)
        assert all(r.failure.kind == FailureKind.CANCELLED.value for r in outcome.results)

    def test_a_cancelled_batch_still_reports_every_file(
        self, monkeypatch, preset, media_files
    ) -> None:
        token = CancellationToken()
        token.cancel()
        install_inspectors(monkeypatch)
        outcome = BatchRunner(startup=STARTUP).run(media_files, preset, token=token)
        assert len(outcome.results) == len(media_files)


class TestCache:
    def test_changing_preset_does_not_re_inspect(
        self, monkeypatch, preset, media_files
    ) -> None:
        """P5-A6 — the expensive part is the subprocess, and it does not depend on rules."""
        calls: list[Path] = []

        def ff(path: Path):
            calls.append(path)
            return InspectorSuccess(raw=ffprobe_payload(video={}, audio={}))

        install_inspectors(monkeypatch, ffprobe_for=ff)
        cache = InspectionCache()
        runner = BatchRunner(startup=STARTUP, cache=cache)

        runner.run(media_files, preset)
        first_pass = len(calls)
        assert first_pass == len(media_files)

        other = build_preset(
            preset_payload(
                preset_id="other_preset",
                rules=[rule("t.height", property_path="video.height", operator="lte", expected=4096)],
            )
        )
        runner.run(media_files, other)
        assert len(calls) == first_pass, "the second run must not re-invoke any inspector"
        assert cache.hits >= len(media_files)

    def test_a_modified_file_is_re_inspected(
        self, monkeypatch, preset, media_files
    ) -> None:
        """The cache key includes size and mtime, so an edited file is not stale."""
        calls: list[Path] = []
        install_inspectors(
            monkeypatch,
            ffprobe_for=lambda p: (
                calls.append(p), InspectorSuccess(raw=ffprobe_payload(video={}, audio={}))
            )[1],
        )
        runner = BatchRunner(startup=STARTUP)
        target = media_files[0]
        runner.run([target], preset)
        target.write_bytes(b"\x01" * 4096)
        runner.run([target], preset)
        assert len(calls) == 2


class TestSourceFilesAreNeverModified:
    def test_bytes_size_and_mtime_are_unchanged_across_a_batch(
        self, monkeypatch, preset, media_files
    ) -> None:
        """P5-A11 / spec AC-13 — the promise a QC tool absolutely must keep."""
        import hashlib

        before = {
            path: (
                hashlib.sha256(path.read_bytes()).hexdigest(),
                path.stat().st_size,
                path.stat().st_mtime_ns,
            )
            for path in media_files
        }

        install_inspectors(monkeypatch)
        BatchRunner(startup=STARTUP).run(media_files, preset)

        after = {
            path: (
                hashlib.sha256(path.read_bytes()).hexdigest(),
                path.stat().st_size,
                path.stat().st_mtime_ns,
            )
            for path in media_files
        }
        assert before == after


class TestMissingInspectors:
    def test_a_missing_inspector_is_reported_not_silently_substituted(
        self, monkeypatch, preset, media_files
    ) -> None:
        """P5-A10 / spec 22.4 — never fall back to a PATH binary."""
        empty = StartupReport(
            inspectors=(
                InspectorInfo(InspectorKind.FFPROBE, None, None, False, "not found"),
                InspectorInfo(InspectorKind.MEDIAINFO, None, None, False, "not found"),
            )
        )
        outcome = BatchRunner(startup=empty).run(media_files[:1], preset)
        result = outcome.results[0]
        assert result.status is FileStatus.NOT_INSPECTED
        assert not empty.usable
