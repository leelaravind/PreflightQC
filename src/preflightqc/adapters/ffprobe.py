"""The ffprobe adapter.

Invokes the bundled ffprobe as a child process and returns a structured outcome.
Never raises; every failure mode has a name in `FailureKind`.

The base invocation reads container and stream metadata only -- no decoding. The
optional HDR pass reads a single frame, which does engage the decoder, and is therefore
**off by default**: the licensing review flags inspection-only decode as a small but
non-zero patent question, and MediaInfo's HDR_Format covers V1's HDR reporting needs
without it.
"""

from __future__ import annotations

import json
from pathlib import Path

from preflightqc.adapters import ffprobe_raw
from preflightqc.adapters.base import (
    FailureKind,
    InspectorFailure,
    InspectorOutcome,
    InspectorSuccess,
    RawInspection,
)
from preflightqc.platform import process
from preflightqc.platform.paths import extended_path

#: Container and stream metadata only. No frames are read, so no decoder is engaged.
BASE_ARGS = (
    "-v", "error",
    "-print_format", "json",
    "-show_format",
    "-show_streams",
    "-show_error",
)

#: Reads exactly one frame of the first video stream to reach frame-attached HDR side
#: data. Opt-in only -- see the module docstring.
HDR_ARGS = ("-show_frames", "-read_intervals", "%+#1", "-select_streams", "v:0")

#: Fragments ffprobe uses when the problem is the file rather than the tool.
_UNREADABLE_MARKERS = ("no such file", "does not exist", "invalid data found")
_PERMISSION_MARKERS = ("permission denied", "access is denied")


def _classify_error(message: str, exit_code: int | None) -> FailureKind:
    lowered = message.lower()
    if any(marker in lowered for marker in _PERMISSION_MARKERS):
        return FailureKind.PERMISSION_DENIED
    if any(marker in lowered for marker in _UNREADABLE_MARKERS):
        return FailureKind.FILE_UNREADABLE
    # A negative or signal-like exit code means the tool died rather than declined.
    if exit_code is not None and exit_code < 0:
        return FailureKind.CRASHED
    return FailureKind.BAD_EXIT


def inspect(
    binary: Path,
    media_path: Path,
    *,
    timeout_seconds: float = 60.0,
    read_hdr_frame: bool = False,
) -> InspectorOutcome:
    """Inspect one file with ffprobe."""
    argv = [str(binary), *BASE_ARGS]
    if read_hdr_frame:
        argv.extend(HDR_ARGS)
    argv.append(extended_path(media_path))

    result = process.run(argv, timeout_seconds=timeout_seconds)

    if result.status is process.RunStatus.TIMEOUT:
        return InspectorFailure(
            kind=FailureKind.TIMEOUT,
            message=f"ffprobe did not finish within {timeout_seconds:g}s",
            duration_ms=result.duration_ms,
        )
    if result.status is process.RunStatus.LAUNCH_FAILED:
        return InspectorFailure(
            kind=FailureKind.LAUNCH_FAILED,
            message=result.message or "ffprobe could not be started",
            duration_ms=result.duration_ms,
        )

    if result.truncated_stdout:
        return InspectorFailure(
            kind=FailureKind.MALFORMED_OUTPUT,
            message="ffprobe output exceeded the capture limit and was truncated",
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
        )

    payload: dict[str, object] | None = None
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            payload = parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError as exc:
            return InspectorFailure(
                kind=FailureKind.MALFORMED_OUTPUT,
                message=f"ffprobe output was not valid JSON: {exc}",
                exit_code=result.exit_code,
                stderr_excerpt=result.stderr[:500] or None,
                duration_ms=result.duration_ms,
            )

    # ffprobe's -show_error puts a structured reason in the JSON body; prefer it over
    # stderr because it is machine-readable and stable.
    if payload is not None:
        structured = ffprobe_raw.extract_error(payload)
        if structured:
            return InspectorFailure(
                kind=_classify_error(structured, result.exit_code),
                message=structured,
                exit_code=result.exit_code,
                stderr_excerpt=result.stderr[:500] or None,
                duration_ms=result.duration_ms,
            )

    if result.exit_code != 0:
        message = result.stderr.strip() or f"ffprobe exited with code {result.exit_code}"
        return InspectorFailure(
            kind=_classify_error(message, result.exit_code),
            message=message,
            exit_code=result.exit_code,
            stderr_excerpt=result.stderr[:500] or None,
            duration_ms=result.duration_ms,
        )

    if payload is None:
        return InspectorFailure(
            kind=FailureKind.MALFORMED_OUTPUT,
            message="ffprobe produced no output",
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
        )

    # A file with no streams at all is not a media file we can validate.
    if not payload.get("streams") and not payload.get("format"):
        return InspectorFailure(
            kind=FailureKind.MALFORMED_OUTPUT,
            message="ffprobe reported neither format nor stream information",
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
        )

    return InspectorSuccess(raw=payload, duration_ms=result.duration_ms)


def parse_outcome(
    outcome: InspectorOutcome, *, tool_version: str | None = None
) -> RawInspection | None:
    """Convert a successful outcome into the common raw intermediate."""
    if not outcome.ok:
        return None
    assert isinstance(outcome, InspectorSuccess)
    return ffprobe_raw.parse(outcome.raw, tool_version=tool_version)
