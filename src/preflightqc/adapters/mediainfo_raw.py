"""Reduce MediaInfo's JSON to the common `RawInspection` intermediate.

Pure: JSON in, typed intermediate out. No I/O, so it is testable without any binary.

MediaInfo is the gap-filler (register section 5): it is the preferred source for scan
type / scan order, frame-rate mode, fast-start, and HDR / Dolby Vision naming, where
ffprobe is documented as weak. Its own documented limitations -- it reads container
flags rather than pixels, and misses Dolby Vision in raw HEVC -- are handled by the
normaliser treating everything here as advisory unless it positively reports a value.
"""

from __future__ import annotations

from typing import Any

from preflightqc.adapters.base import RawInspection, RawStream

_NA_TOKENS = frozenset({"", "N/A", "n/a", "Unknown", "unknown"})


def _clean(value: Any) -> Any:
    if isinstance(value, str) and value.strip() in _NA_TOKENS:
        return None
    return value


def _tracks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    media = payload.get("media")
    if not isinstance(media, dict):
        return []
    tracks = media.get("track")
    if isinstance(tracks, dict):  # a single-track file is emitted as an object
        return [tracks]
    if isinstance(tracks, list):
        return [t for t in tracks if isinstance(t, dict)]
    return []


def _kind(track_type: str) -> str:
    return {
        "Video": "video",
        "Audio": "audio",
        "Text": "subtitle",
        "General": "general",
    }.get(track_type, "other")


def _is_streamable(general: dict[str, Any]) -> bool | None:
    """MediaInfo's IsStreamable is the most reliable fast-start signal available.

    ffprobe exposes no direct equivalent, so this is the precedence winner for
    `container.faststart` (register section 5).
    """
    value = general.get("IsStreamable")
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"yes", "true", "1"}


def parse(payload: dict[str, Any], *, tool_version: str | None = None) -> RawInspection:
    """Convert a MediaInfo `--Output=JSON` payload into a `RawInspection`."""
    tracks = _tracks(payload)
    general = next((t for t in tracks if _kind(str(t.get("@type", ""))) == "general"), {})

    version = tool_version
    if version is None:
        creating = payload.get("creatingLibrary")
        if isinstance(creating, dict) and creating.get("version"):
            version = str(creating["version"])

    container: dict[str, Any] = {
        "Format": _clean(general.get("Format")),
        "Format_Profile": _clean(general.get("Format_Profile")),
        "CodecID": _clean(general.get("CodecID")),
        "Duration": _clean(general.get("Duration")),
        "FileSize": _clean(general.get("FileSize")),
        "OverallBitRate": _clean(general.get("OverallBitRate")),
        "IsStreamable": _is_streamable(general),
        "VideoCount": _clean(general.get("VideoCount")),
        "AudioCount": _clean(general.get("AudioCount")),
    }

    streams: list[RawStream] = []
    index = 0
    for track in tracks:
        kind = _kind(str(track.get("@type", "")))
        if kind in ("general", "other"):
            continue
        fields: dict[str, Any] = {
            key: _clean(track.get(key))
            for key in (
                "Format",
                "Format_Profile",
                "Format_Level",
                "CodecID",
                "Width",
                "Height",
                "Stored_Width",
                "Stored_Height",
                "PixelAspectRatio",
                "DisplayAspectRatio",
                "FrameRate",
                "FrameRate_Mode",
                "FrameRate_Num",
                "FrameRate_Den",
                "BitRate",
                "BitRate_Mode",
                "BitDepth",
                "ChromaSubsampling",
                "ScanType",
                "ScanOrder",
                "colour_range",
                "colour_primaries",
                "transfer_characteristics",
                "matrix_coefficients",
                "HDR_Format",
                "HDR_Format_Commercial",
                "HDR_Format_Profile",
                "HDR_Format_Compatibility",
                "MaxCLL",
                "MaxFALL",
                "Rotation",
                "SamplingRate",
                "Channels",
                "ChannelLayout",
                "ChannelPositions",
                "Duration",
            )
        }
        streams.append(RawStream(index=index, kind=kind, fields=fields))
        index += 1

    return RawInspection(
        inspector="mediainfo",
        tool_version=version,
        container=container,
        streams=tuple(streams),
    )
