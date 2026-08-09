"""The MediaInfo adapter.

MediaInfo is the gap-filler: scan type and scan order, frame-rate mode, fast start, and
clean HDR / Dolby Vision naming, all of which ffprobe handles weakly or not at all.

Invoked as a **subprocess** rather than in-process through the library. Licensing is
neutral between the two (both are BSD-2-Clause), so the decision is an engineering one:
PreflightQC ingests files of unknown provenance, and a parser crash or hang inside our
own address space would take the whole application down mid-batch. Process isolation
costs a spawn per file and buys us a batch that survives a hostile input.
"""

from __future__ import annotations

import json
from pathlib import Path

from preflightqc.adapters import mediainfo_raw
from preflightqc.adapters.base import (
    FailureKind,
    InspectorFailure,
    InspectorOutcome,
    InspectorSuccess,
    RawInspection,
)
from preflightqc.platform import process
from preflightqc.platform.paths import extended_path

#: JSON output is the only stable machine-readable form; the default text output is a
#: human report whose layout changes between versions.
BASE_ARGS = ("--Output=JSON",)

_PERMISSION_MARKERS = ("permission denied", "access is denied")
_UNREADABLE_MARKERS = ("unable to load", "no such file", "cannot open", "file not found")


def _classify_error(message: str) -> FailureKind:
    lowered = message.lower()
    if any(marker in lowered for marker in _PERMISSION_MARKERS):
        return FailureKind.PERMISSION_DENIED
    if any(marker in lowered for marker in _UNREADABLE_MARKERS):
        return FailureKind.FILE_UNREADABLE
    return FailureKind.BAD_EXIT


def inspect(
    binary: Path,
    media_path: Path,
    *,
    timeout_seconds: float = 60.0,
) -> InspectorOutcome:
    """Inspect one file with MediaInfo."""
    argv = [str(binary), *BASE_ARGS, extended_path(media_path)]
    result = process.run(argv, timeout_seconds=timeout_seconds)

    if result.status is process.RunStatus.TIMEOUT:
        return InspectorFailure(
            kind=FailureKind.TIMEOUT,
            message=f"MediaInfo did not finish within {timeout_seconds:g}s",
            duration_ms=result.duration_ms,
        )
    if result.status is process.RunStatus.LAUNCH_FAILED:
        return InspectorFailure(
            kind=FailureKind.LAUNCH_FAILED,
            message=result.message or "MediaInfo could not be started",
            duration_ms=result.duration_ms,
        )
    if result.truncated_stdout:
        return InspectorFailure(
            kind=FailureKind.MALFORMED_OUTPUT,
            message="MediaInfo output exceeded the capture limit and was truncated",
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
        )

    if not result.stdout.strip():
        message = result.stderr.strip() or "MediaInfo produced no output"
        return InspectorFailure(
            kind=_classify_error(message),
            message=message,
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
        )

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return InspectorFailure(
            kind=FailureKind.MALFORMED_OUTPUT,
            message=f"MediaInfo output was not valid JSON: {exc}",
            exit_code=result.exit_code,
            stderr_excerpt=result.stderr[:500] or None,
            duration_ms=result.duration_ms,
        )

    if not isinstance(parsed, dict) or "media" not in parsed:
        # MediaInfo emits a JSON document without a "media" key when it could not read
        # the file at all -- a different fact from "the file has no streams".
        return InspectorFailure(
            kind=FailureKind.FILE_UNREADABLE,
            message="MediaInfo could not read any media information from the file",
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
        )

    return InspectorSuccess(raw=parsed, duration_ms=result.duration_ms)


def parse_outcome(
    outcome: InspectorOutcome, *, tool_version: str | None = None
) -> RawInspection | None:
    """Convert a successful outcome into the common raw intermediate."""
    if not outcome.ok:
        return None
    assert isinstance(outcome, InspectorSuccess)
    return mediainfo_raw.parse(outcome.raw, tool_version=tool_version)
