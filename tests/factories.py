"""Builders for test data.

Two kinds of factory live here:

* `ffprobe_payload` / `mediainfo_payload` build realistic **raw inspector JSON**, so the
  normaliser is tested against the shape the real tools emit.
* `preset_payload` / `rule` build **preset documents**, so engine tests can express a
  rule inline instead of carrying fixture files around.

Keeping both here means a change to either shape is a one-file edit.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from preflightqc.adapters import ffprobe_raw, mediainfo_raw
from preflightqc.core.model import NormalisedMedia
from preflightqc.normalise.normaliser import normalise

# ---------------------------------------------------------------------------
# Raw inspector payloads
# ---------------------------------------------------------------------------


def ffprobe_payload(
    *,
    format_name: str = "mov,mp4,m4a,3gp,3g2,mj2",
    duration: str | None = "30.000000",
    size: str | None = "10000000",
    bit_rate: str | None = "2666666",
    major_brand: str = "isom",
    video: dict[str, Any] | None = None,
    audio: dict[str, Any] | None = None,
    extra_streams: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """A realistic ffprobe `-print_format json` payload."""
    streams: list[dict[str, Any]] = []
    if video is not None:
        base_video: dict[str, Any] = {
            "index": 0,
            "codec_type": "video",
            "codec_name": "h264",
            "codec_tag_string": "avc1",
            "profile": "High",
            "level": 40,
            "width": 1080,
            "height": 1920,
            "coded_width": 1080,
            "coded_height": 1920,
            "sample_aspect_ratio": "1:1",
            "display_aspect_ratio": "9:16",
            "pix_fmt": "yuv420p",
            "field_order": "progressive",
            "r_frame_rate": "30/1",
            "avg_frame_rate": "30/1",
            "bit_rate": "2500000",
            "color_range": "tv",
            "color_space": "bt709",
            "color_transfer": "bt709",
            "color_primaries": "bt709",
        }
        base_video.update(video)
        streams.append(base_video)
    if audio is not None:
        base_audio: dict[str, Any] = {
            "index": len(streams),
            "codec_type": "audio",
            "codec_name": "aac",
            "sample_rate": "48000",
            "channels": 2,
            "channel_layout": "stereo",
            "bit_rate": "128000",
            "duration": duration,
        }
        base_audio.update(audio)
        streams.append(base_audio)
    if extra_streams:
        streams.extend(extra_streams)

    payload: dict[str, Any] = {
        "streams": streams,
        "format": {
            "format_name": format_name,
            "format_long_name": "QuickTime / MOV",
            "nb_streams": len(streams),
            "tags": {"major_brand": major_brand, "compatible_brands": "isomiso2avc1mp41"},
        },
    }
    for key, value in (("duration", duration), ("size", size), ("bit_rate", bit_rate)):
        if value is not None:
            payload["format"][key] = value
    return payload


def mediainfo_payload(
    *,
    fmt: str = "MPEG-4",
    duration: str | None = "30.000",
    file_size: str | None = "10000000",
    is_streamable: str = "Yes",
    video: dict[str, Any] | None = None,
    audio: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """A realistic MediaInfo `--Output=JSON` payload."""
    tracks: list[dict[str, Any]] = [
        {
            "@type": "General",
            "Format": fmt,
            "CodecID": "isom",
            "IsStreamable": is_streamable,
            "VideoCount": "1" if video is not None else "0",
            "AudioCount": "1" if audio is not None else "0",
        }
    ]
    if duration is not None:
        tracks[0]["Duration"] = duration
    if file_size is not None:
        tracks[0]["FileSize"] = file_size

    if video is not None:
        base_video: dict[str, Any] = {
            "@type": "Video",
            "Format": "AVC",
            "Format_Profile": "High@L4",
            "Width": "1080",
            "Height": "1920",
            "FrameRate": "30.000",
            "FrameRate_Mode": "CFR",
            "BitRate": "2500000",
            "BitDepth": "8",
            "ChromaSubsampling": "4:2:0",
            "ScanType": "Progressive",
            "colour_range": "Limited",
        }
        base_video.update(video)
        tracks.append(base_video)
    if audio is not None:
        base_audio: dict[str, Any] = {
            "@type": "Audio",
            "Format": "AAC",
            "SamplingRate": "48000",
            "Channels": "2",
            "ChannelLayout": "L R",
            "BitRate": "128000",
        }
        base_audio.update(audio)
        tracks.append(base_audio)

    return {"creatingLibrary": {"version": "26.05"}, "media": {"track": tracks}}


def build_media(
    *,
    path: Path | None = None,
    ffprobe: dict[str, Any] | None = None,
    mediainfo: dict[str, Any] | None = None,
    size_bytes: int | None = 10_000_000,
) -> NormalisedMedia:
    """Normalise a pair of raw payloads into the model, the way the app does."""
    ff = ffprobe_raw.parse(ffprobe, tool_version="7.1") if ffprobe is not None else None
    mi = mediainfo_raw.parse(mediainfo, tool_version="26.05") if mediainfo is not None else None
    return normalise(
        path or Path("C:/clips/sample.mp4"),
        ffprobe=ff,
        mediainfo=mi,
        size_bytes=size_bytes,
    )


def default_media(**overrides: Any) -> NormalisedMedia:
    """A conformant 1080x1920, 30 fps, H.264 + AAC file -- the happy path."""
    ff = ffprobe_payload(video=overrides.pop("video", {}), audio=overrides.pop("audio", {}))
    mi = mediainfo_payload(video={}, audio={})
    return build_media(ffprobe=ff, mediainfo=mi, **overrides)


# ---------------------------------------------------------------------------
# Preset payloads
# ---------------------------------------------------------------------------


def source_entry(source_ref: str = "S1", confidence: str = "HIGH") -> dict[str, Any]:
    return {
        "source_ref": source_ref,
        "title": "Test source",
        "url": "https://example.invalid/spec",
        "access_date": "2026-08-09",
        "confidence": confidence,
    }


def rule(
    rule_id: str = "test.rule",
    *,
    property_path: str = "video.width",
    operator: str = "lte",
    expected: Any = 1920,
    classification: str = "HARD_REQUIREMENT",
    severity: str = "FAIL",
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "rule_id": rule_id,
        "property": property_path,
        "operator": operator,
        "classification": classification,
        "severity": severity,
        "explanation": "A test rule.",
        "source_ref": "S1",
        "confidence": "HIGH",
        "last_verified_date": "2026-08-09",
    }
    if expected is not None:
        payload["expected"] = expected
    payload.update(extra)
    return payload


def preset_payload(
    *,
    preset_id: str = "test_preset",
    platform: str = "Test",
    rules: list[dict[str, Any]] | None = None,
    sources: list[dict[str, Any]] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "preset_id": preset_id,
        "platform": platform,
        "display_name": "Test Preset",
        "description": "A preset used only by the test suite.",
        "ruleset_version": "2026-08-09.1",
        "last_verified_date": "2026-08-09",
        # `is not None`, not truthiness: a test that passes [] is asserting that an
        # empty block is rejected, and must not be silently handed the default.
        "sources": sources if sources is not None else [source_entry()],
        "rules": rules if rules is not None else [rule()],
    }
    payload.update(extra)
    return payload
