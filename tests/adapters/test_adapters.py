"""Phase 5 — adapter failure taxonomy.

The process runner is exercised for real elsewhere; here the runner is replaced with
canned results so every branch of the classification logic can be reached, including
the ones a real inspector would only produce for a genuinely corrupt file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from factories import ffprobe_payload, mediainfo_payload
from preflightqc.adapters import ffprobe, mediainfo
from preflightqc.adapters.base import FailureKind, InspectorFailure, InspectorSuccess
from preflightqc.platform import process
from preflightqc.platform.process import RunResult, RunStatus

BINARY = Path("C:/app/bin/ffprobe.exe")
MEDIA = Path("C:/clips/sample.mp4")


def canned(
    monkeypatch,
    *,
    stdout: str = "",
    stderr: str = "",
    exit_code: int = 0,
    status: RunStatus = RunStatus.COMPLETED,
    truncated: bool = False,
    message: str = "",
    module=process,
) -> None:
    def fake_run(argv, **kwargs):
        return RunResult(
            status=status,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=1.0,
            truncated_stdout=truncated,
            message=message,
        )

    monkeypatch.setattr(module, "run", fake_run)


class TestFfprobeSuccess:
    def test_valid_output_parses(self, monkeypatch) -> None:
        canned(monkeypatch, stdout=json.dumps(ffprobe_payload(video={}, audio={})))
        outcome = ffprobe.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorSuccess)
        assert outcome.ok
        raw = ffprobe.parse_outcome(outcome, tool_version="7.1")
        assert raw is not None
        assert raw.inspector == "ffprobe"
        assert raw.streams_of("video")

    def test_the_hdr_pass_is_opt_in(self, monkeypatch) -> None:
        """The only operation that engages the decoder must not run by default."""
        seen: list[list[str]] = []

        def capture(argv, **kwargs):
            seen.append(argv)
            return RunResult(RunStatus.COMPLETED, 0, json.dumps(ffprobe_payload(video={})), "", 1.0)

        monkeypatch.setattr(process, "run", capture)

        ffprobe.inspect(BINARY, MEDIA)
        assert "-show_frames" not in seen[0]

        ffprobe.inspect(BINARY, MEDIA, read_hdr_frame=True)
        assert "-show_frames" in seen[1]
        assert "-read_intervals" in seen[1]


class TestFfprobeFailures:
    def test_timeout(self, monkeypatch) -> None:
        canned(monkeypatch, status=RunStatus.TIMEOUT, exit_code=None)
        outcome = ffprobe.inspect(BINARY, MEDIA, timeout_seconds=5)
        assert isinstance(outcome, InspectorFailure)
        assert outcome.kind is FailureKind.TIMEOUT

    def test_launch_failure(self, monkeypatch) -> None:
        canned(monkeypatch, status=RunStatus.LAUNCH_FAILED, exit_code=None, message="not found")
        outcome = ffprobe.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)
        assert outcome.kind is FailureKind.LAUNCH_FAILED

    def test_malformed_json(self, monkeypatch) -> None:
        canned(monkeypatch, stdout='{"streams": [ ')
        outcome = ffprobe.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)
        assert outcome.kind is FailureKind.MALFORMED_OUTPUT

    def test_truncated_output(self, monkeypatch) -> None:
        canned(monkeypatch, stdout="{}", truncated=True)
        outcome = ffprobe.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)
        assert outcome.kind is FailureKind.MALFORMED_OUTPUT

    def test_empty_output(self, monkeypatch) -> None:
        canned(monkeypatch, stdout="")
        outcome = ffprobe.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)

    def test_structured_error_for_a_missing_file(self, monkeypatch) -> None:
        canned(
            monkeypatch,
            stdout=json.dumps({"error": {"code": -2, "string": "No such file or directory"}}),
            exit_code=1,
        )
        outcome = ffprobe.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)
        assert outcome.kind is FailureKind.FILE_UNREADABLE

    def test_structured_error_for_permission_denied(self, monkeypatch) -> None:
        canned(
            monkeypatch,
            stdout=json.dumps({"error": {"code": -13, "string": "Permission denied"}}),
            exit_code=1,
        )
        outcome = ffprobe.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)
        assert outcome.kind is FailureKind.PERMISSION_DENIED

    def test_corrupt_file_reports_invalid_data(self, monkeypatch) -> None:
        canned(
            monkeypatch,
            stdout=json.dumps({"error": {"code": -1094995529, "string": "Invalid data found"}}),
            exit_code=1,
        )
        outcome = ffprobe.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)
        assert outcome.kind is FailureKind.FILE_UNREADABLE

    def test_a_negative_exit_code_reads_as_a_crash(self, monkeypatch) -> None:
        canned(monkeypatch, stdout="", stderr="Segmentation fault", exit_code=-11)
        outcome = ffprobe.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)
        assert outcome.kind is FailureKind.CRASHED

    def test_a_document_with_neither_format_nor_streams_is_rejected(self, monkeypatch) -> None:
        canned(monkeypatch, stdout=json.dumps({"programs": []}))
        outcome = ffprobe.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)


class TestMediaInfo:
    def test_valid_output_parses(self, monkeypatch) -> None:
        canned(monkeypatch, stdout=json.dumps(mediainfo_payload(video={}, audio={})))
        outcome = mediainfo.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorSuccess)
        raw = mediainfo.parse_outcome(outcome)
        assert raw is not None
        assert raw.tool_version == "26.05"
        assert raw.container["IsStreamable"] is True

    def test_json_output_is_requested(self, monkeypatch) -> None:
        """The default text output is a human report whose layout is not stable."""
        seen: list[list[str]] = []

        def capture(argv, **kwargs):
            seen.append(argv)
            return RunResult(RunStatus.COMPLETED, 0, json.dumps(mediainfo_payload(video={})), "", 1.0)

        monkeypatch.setattr(process, "run", capture)
        mediainfo.inspect(BINARY, MEDIA)
        assert "--Output=JSON" in seen[0]

    def test_a_document_without_a_media_key_is_unreadable(self, monkeypatch) -> None:
        canned(monkeypatch, stdout=json.dumps({"creatingLibrary": {"version": "26.05"}}))
        outcome = mediainfo.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)
        assert outcome.kind is FailureKind.FILE_UNREADABLE

    def test_malformed_json(self, monkeypatch) -> None:
        canned(monkeypatch, stdout="not json at all")
        outcome = mediainfo.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)
        assert outcome.kind is FailureKind.MALFORMED_OUTPUT

    def test_timeout(self, monkeypatch) -> None:
        canned(monkeypatch, status=RunStatus.TIMEOUT, exit_code=None)
        outcome = mediainfo.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)
        assert outcome.kind is FailureKind.TIMEOUT

    def test_no_output_is_classified_from_stderr(self, monkeypatch) -> None:
        canned(monkeypatch, stdout="", stderr="Permission denied", exit_code=1)
        outcome = mediainfo.inspect(BINARY, MEDIA)
        assert isinstance(outcome, InspectorFailure)
        assert outcome.kind is FailureKind.PERMISSION_DENIED


@pytest.mark.parametrize("adapter", [ffprobe, mediainfo])
def test_adapters_never_raise(monkeypatch, adapter) -> None:
    """The contract the batch depends on."""
    for stdout, code, status in (
        ("", 0, RunStatus.COMPLETED),
        ("garbage", 1, RunStatus.COMPLETED),
        ("", None, RunStatus.TIMEOUT),
        ("", None, RunStatus.LAUNCH_FAILED),
        ("{}", 0, RunStatus.COMPLETED),
    ):
        canned(monkeypatch, stdout=stdout, exit_code=code, status=status)
        outcome = adapter.inspect(BINARY, MEDIA)
        assert hasattr(outcome, "ok")
