"""Synthetic media construction for boundary testing.

The plan's preferred Phase 9 corpus is generated media. That is blocked: the
development-only encoder is not present on this machine
(`docs/planning/SPIKE-01-INSPECTOR-FINDINGS.md`), so no real fixture can be produced.

The test strategy anticipates exactly this and authorises the fallback in section 3.5:
cover the boundary against a **synthetic NormalisedMedia** instead, and record the
exception rather than silently skipping the rule.

What this loses: it does not prove ffprobe reports the value we think it does. What it
keeps — and what the boundary corpus is actually for — is proof that each shipped rule
fires at exactly the threshold its source states, and not one unit earlier or later.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

from preflightqc.core.model import (
    PROPERTY_PATHS,
    AudioStream,
    ContainerInfo,
    Diagnostics,
    FileInfo,
    NormalisedMedia,
    VideoStream,
)
from preflightqc.core.values import MetaField, Provenance

SYNTHETIC = Provenance(inspector="synthetic", field_path="test-fixture")


def _known(value: Any) -> MetaField[Any]:
    return MetaField.known(value, SYNTHETIC)


def _absent(reason: str = "not set by this fixture") -> MetaField[Any]:
    return MetaField.undetermined(reason)


def blank_video(index: int = 0) -> VideoStream:
    return VideoStream(
        index=index,
        codec=_absent(),
        profile=_absent(),
        level=_absent(),
        width=_absent(),
        height=_absent(),
        coded_width=_absent(),
        coded_height=_absent(),
        display_width=_absent(),
        display_height=_absent(),
        sample_aspect_ratio=_absent(),
        display_aspect_ratio=_absent(),
        rotation_degrees=_known(0),
        frame_rate=_absent(),
        frame_rate_mode=_absent(),
        bitrate=_absent(),
        bitrate_source=_absent(),
        pixel_format=_absent(),
        bit_depth=_absent(),
        chroma_subsampling=_absent(),
        scan_type=_absent(),
        colour_range=_absent(),
        colour_space=_absent(),
        transfer_characteristics=_absent(),
        colour_primaries=_absent(),
        gop_closed=_absent(),
        hdr_format=_absent(),
        dolby_vision=_absent(),
        max_cll=_absent(),
        max_fall=_absent(),
    )


def blank_audio(index: int = 0) -> AudioStream:
    return AudioStream(
        index=index,
        codec=_absent(),
        sample_rate=_absent(),
        channels=_absent(),
        channel_layout=_absent(),
        bitrate=_absent(),
        duration_seconds=_absent(),
    )


def blank_container() -> ContainerInfo:
    return ContainerInfo(
        formats=_absent(),
        format_long_name=_absent(),
        major_brand=_absent(),
        compatible_brands=_absent(),
        stream_count=_absent(),
        video_stream_count=_absent(),
        audio_stream_count=_absent(),
        overall_bitrate=_absent(),
        faststart=_absent(),
        edit_lists_present=_absent(),
    )


def blank_media(path: Path | None = None) -> NormalisedMedia:
    """A model where every field is UNDETERMINED.

    Every rule evaluated against this must produce UNKNOWN and never FAIL — which is
    itself one of the properties the corpus proves.
    """
    return NormalisedMedia(
        file=FileInfo(
            path=path or Path("C:/synthetic/fixture.mp4"),
            name="fixture.mp4",
            size_bytes=_absent(),
            duration_seconds=_absent(),
        ),
        container=blank_container(),
        video=(blank_video(),),
        audio=(blank_audio(),),
        diagnostics=Diagnostics(),
    )


#: Where each property path lives in the model, so a single value can be injected.
_SECTION = {
    "file": "file",
    "container": "container",
    "video": "video",
    "audio": "audio",
}


def media_with(property_path: str, value: Any, *, base: NormalisedMedia | None = None) -> NormalisedMedia:
    """A model identical to `base` except that one property holds `value`."""
    if property_path not in PROPERTY_PATHS:
        raise KeyError(property_path)

    media = base or blank_media()
    section, _, attribute = property_path.partition(".")

    # `audio.present` is derived from stream enumeration, not stored as a field.
    if property_path == "audio.present":
        return replace(media, audio=(blank_audio(),) if value else ())

    field = _known(value)
    if section == "file":
        return replace(media, file=replace(media.file, **{attribute: field}))
    if section == "container":
        name = "formats" if attribute == "format" else attribute
        return replace(media, container=replace(media.container, **{name: field}))
    if section == "video":
        streams = media.video or (blank_video(),)
        return replace(media, video=(replace(streams[0], **{attribute: field}), *streams[1:]))
    if section == "audio":
        streams = media.audio or (blank_audio(),)
        return replace(media, audio=(replace(streams[0], **{attribute: field}), *streams[1:]))
    raise KeyError(property_path)  # pragma: no cover - guarded by PROPERTY_PATHS


# ---------------------------------------------------------------------------
# Boundary derivation
# ---------------------------------------------------------------------------

#: A container token no preset lists, used as the "outside" value for container rules.
UNLISTED_CONTAINER = frozenset({"unlisted_container_format"})
UNLISTED_TOKEN = "unlisted_token_value"


def _step(value: float, property_path: str) -> float:
    """The smallest meaningful step outside a numeric bound.

    Pixel counts, byte counts and channel counts are integers, so one unit is the real
    boundary. Continuous quantities get a small fraction, which is what "just outside"
    means for a duration or a frame rate.
    """
    if property_path in {
        "video.display_width",
        "video.display_height",
        "video.width",
        "video.height",
        "file.size_bytes",
        "audio.channels",
        "audio.sample_rate",
        "video.bit_depth",
        "video.bitrate",
        "audio.bitrate",
        "container.overall_bitrate",
    }:
        return 1.0
    return max(abs(value) * 0.01, 0.01)


def _coerce(property_path: str, value: float) -> Any:
    """Present a numeric boundary in the type the model actually stores."""
    if property_path in {"video.frame_rate", "video.display_aspect_ratio", "video.sample_aspect_ratio"}:
        return Fraction(value).limit_denominator(100000)
    if property_path in {"file.duration_seconds", "audio.duration_seconds"}:
        return float(value)
    return int(round(value))


def _satisfying_value(guard) -> Any:
    """A value that makes a guard true, so a guarded rule can be reached at all.

    Without this, every conditional rule (HDR, per-ratio minimum dimensions) would be
    skipped by its own guard and its boundary would go untested — which is exactly the
    silent coverage hole the corpus exists to prevent.
    """
    path, operator, expected = guard.property_path, guard.operator, guard.expected
    if operator == "in":
        if path == "container.format":
            return frozenset({expected[0]})
        value = expected[0]
        return _coerce(path, float(value)) if isinstance(value, int | float) else value
    if operator == "not_in":
        return UNLISTED_CONTAINER if path == "container.format" else UNLISTED_TOKEN
    if operator == "eq":
        return expected if not isinstance(expected, int | float) else _coerce(path, float(expected))
    if operator == "range" and isinstance(expected, dict):
        low, high = expected.get("min"), expected.get("max")
        if low is not None and high is not None:
            return _coerce(path, (float(low) + float(high)) / 2)
        if low is not None:
            return _coerce(path, float(low) + _step(float(low), path))
        return _coerce(path, float(high) - _step(float(high), path))
    if operator in {"lte", "lt"}:
        return _coerce(path, float(expected) - _step(float(expected), path))
    if operator in {"gte", "gt"}:
        return _coerce(path, float(expected) + _step(float(expected), path))
    if operator == "constant_only":
        return "CFR"
    return "some-value"


def media_satisfying_guards(rule, *, base: NormalisedMedia | None = None) -> NormalisedMedia:
    """A model in which every one of the rule's guards evaluates true."""
    media = base or blank_media()
    for guard in rule.guards:
        media = media_with(guard.property_path, _satisfying_value(guard), base=media)
    return media


def boundary_values(rule) -> list[tuple[str, Any, bool]]:
    """Derive (label, value, should_pass) cases for one rule.

    Returns an empty list for rules whose boundary is not a single scalar the model can
    hold — those are covered by dedicated tests instead of by derivation.
    """
    path = rule.property_path
    operator = rule.operator
    expected = rule.expected
    tolerance = rule.tolerance or 0.0
    relative = rule.relative_tolerance
    cases: list[tuple[str, Any, bool]] = []

    def numeric_edge(bound: float, *, inside_is_bound: bool, above: bool) -> None:
        step = _step(bound, path)
        if relative and tolerance:
            slack = bound * tolerance
        else:
            slack = tolerance
        inside = bound if inside_is_bound else (bound - step if above else bound + step)
        outside = (bound + slack + step) if above else (bound - slack - step)
        cases.append((f"inside@{bound}", _coerce(path, inside), True))
        cases.append((f"outside@{bound}", _coerce(path, outside), False))

    match operator:
        case "lte":
            numeric_edge(float(expected), inside_is_bound=True, above=True)
        case "lt":
            numeric_edge(float(expected), inside_is_bound=False, above=True)
        case "gte":
            numeric_edge(float(expected), inside_is_bound=True, above=False)
        case "gt":
            numeric_edge(float(expected), inside_is_bound=False, above=False)
        case "range":
            if isinstance(expected, dict):
                if expected.get("min") is not None:
                    numeric_edge(float(expected["min"]), inside_is_bound=True, above=False)
                if expected.get("max") is not None:
                    numeric_edge(float(expected["max"]), inside_is_bound=True, above=True)
        case "in":
            if path == "container.format":
                cases.append(("inside", frozenset({expected[0]}), True))
                cases.append(("outside", UNLISTED_CONTAINER, False))
            elif all(isinstance(v, int | float) for v in expected):
                cases.append(("inside", _coerce(path, float(expected[0])), True))
                cases.append(("outside", _coerce(path, float(max(expected)) + 1000), False))
            else:
                cases.append(("inside", expected[0], True))
                cases.append(("outside", UNLISTED_TOKEN, False))
        case "not_in":
            cases.append(("inside", UNLISTED_TOKEN, True))
            cases.append(("outside", expected[0], False))
        case "eq":
            if isinstance(expected, bool):
                cases.append(("inside", expected, True))
                cases.append(("outside", not expected, False))
            elif isinstance(expected, int | float):
                slack = (expected * tolerance) if relative and tolerance else tolerance
                cases.append(("inside", _coerce(path, float(expected)), True))
                cases.append(
                    ("outside", _coerce(path, float(expected) + slack + _step(float(expected), path)), False)
                )
            else:
                cases.append(("inside", expected, True))
                cases.append(("outside", UNLISTED_TOKEN, False))
        case "constant_only":
            cases.append(("inside", "CFR", True))
            cases.append(("outside", "VFR", False))
        case "present":
            cases.append(("inside", "some-value", True))
    return cases
