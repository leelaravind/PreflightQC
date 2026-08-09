"""Reduce ffprobe's JSON to the common `RawInspection` intermediate.

This module is pure: JSON in, typed intermediate out. It performs no I/O, so it is
testable against captured fixtures without any binary present.

It deliberately does **not** canonicalise values. "yuv420p" stays "yuv420p" here; the
normaliser decides what that means. Keeping the two apart means a vocabulary change
never requires touching parsing.
"""

from __future__ import annotations

from typing import Any

from preflightqc.adapters.base import RawInspection, RawStream

#: ffprobe writes "N/A" for values it has no answer for. Treated as absent, never as text.
_NA_TOKENS = frozenset({"N/A", "n/a", "", "unknown"})


def _clean(value: Any) -> Any:
    """Drop ffprobe's placeholder values so absence stays absence."""
    if isinstance(value, str) and value.strip() in _NA_TOKENS:
        return None
    return value


def _stream_kind(stream: dict[str, Any]) -> str:
    codec_type = stream.get("codec_type")
    if codec_type in ("video", "audio", "subtitle", "data"):
        # ffprobe reports attached cover art as a video stream with a still-image codec
        # and a disposition flag. Counting it as a video stream would make an audio file
        # with artwork look like a video, and would make a normal video look
        # multi-stream. Classify it separately.
        if codec_type == "video" and stream.get("disposition", {}).get("attached_pic") == 1:
            return "other"
        return str(codec_type)
    return "other"


def _rotation_from_stream(stream: dict[str, Any]) -> float | None:
    """Extract rotation from either the display-matrix side data or the legacy tag.

    ffprobe reports display-matrix rotation as the angle needed to *undo* the
    transform, which is why the sign is negated here to yield the clockwise
    presentation rotation editors expect.
    """
    for side_data in stream.get("side_data_list", []) or []:
        if not isinstance(side_data, dict):
            continue
        if side_data.get("side_data_type") == "Display Matrix" and "rotation" in side_data:
            try:
                return -float(side_data["rotation"])
            except (TypeError, ValueError):
                continue
    tag = stream.get("tags", {}).get("rotate")
    if tag is not None:
        try:
            return float(tag)
        except (TypeError, ValueError):
            return None
    return None


def _hdr_side_data(stream: dict[str, Any]) -> dict[str, Any]:
    """Collect the HDR facts ffprobe exposes as frame or stream side data."""
    found: dict[str, Any] = {}
    for side_data in stream.get("side_data_list", []) or []:
        if not isinstance(side_data, dict):
            continue
        kind = side_data.get("side_data_type", "")
        if kind == "Content light level metadata":
            if "max_content" in side_data:
                found["max_cll"] = side_data["max_content"]
            if "max_average" in side_data:
                found["max_fall"] = side_data["max_average"]
        elif kind == "Mastering display metadata":
            found["mastering_display"] = True
        elif "Dolby Vision" in kind or kind == "DOVI configuration record":
            profile = side_data.get("dv_profile")
            found["dolby_vision"] = (
                f"dvhe.{profile:02d}" if isinstance(profile, int) else "Dolby Vision"
            )
        elif kind == "HDR Dynamic Metadata SMPTE2094-40 (HDR10+)":
            found["hdr10_plus"] = True
    return found


def parse(payload: dict[str, Any], *, tool_version: str | None = None) -> RawInspection:
    """Convert an ffprobe `-print_format json` payload into a `RawInspection`."""
    fmt = payload.get("format", {}) or {}
    tags = fmt.get("tags", {}) or {}

    container: dict[str, Any] = {
        "format_name": _clean(fmt.get("format_name")),
        "format_long_name": _clean(fmt.get("format_long_name")),
        "duration": _clean(fmt.get("duration")),
        "size": _clean(fmt.get("size")),
        "bit_rate": _clean(fmt.get("bit_rate")),
        "nb_streams": fmt.get("nb_streams"),
        "major_brand": _clean(tags.get("major_brand")),
        "compatible_brands": _clean(tags.get("compatible_brands")),
        "tags": {str(k): str(v) for k, v in tags.items()},
    }

    streams: list[RawStream] = []
    for raw_stream in payload.get("streams", []) or []:
        if not isinstance(raw_stream, dict):
            continue
        kind = _stream_kind(raw_stream)
        fields: dict[str, Any] = {
            key: _clean(raw_stream.get(key))
            for key in (
                "codec_name",
                "codec_long_name",
                "codec_tag_string",
                "profile",
                "level",
                "width",
                "height",
                "coded_width",
                "coded_height",
                "sample_aspect_ratio",
                "display_aspect_ratio",
                "pix_fmt",
                "field_order",
                "r_frame_rate",
                "avg_frame_rate",
                "bit_rate",
                "bits_per_raw_sample",
                "color_range",
                "color_space",
                "color_transfer",
                "color_primaries",
                "sample_rate",
                "channels",
                "channel_layout",
                "duration",
                "nb_frames",
            )
        }
        rotation = _rotation_from_stream(raw_stream)
        if rotation is not None:
            fields["rotation"] = rotation
        fields.update(_hdr_side_data(raw_stream))
        streams.append(
            RawStream(index=int(raw_stream.get("index", len(streams))), kind=kind, fields=fields)
        )

    return RawInspection(
        inspector="ffprobe",
        tool_version=tool_version,
        container=container,
        streams=tuple(streams),
    )


def extract_error(payload: dict[str, Any]) -> str | None:
    """Return ffprobe's structured error message, if `-show_error` produced one."""
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("string") or error.get("message")
        if message:
            return str(message)
        return f"ffprobe error code {error.get('code')}"
    return None
