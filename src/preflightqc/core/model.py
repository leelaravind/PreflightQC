"""The normalised metadata model.

One concrete model, not an interface hierarchy (ARCHITECTURE-V1.md section 20). Every
field is a `MetaField`, so absence is always explicit.

The module also defines `PROPERTY_PATHS`: the canonical dotted paths a preset rule may
target. Resolving a rule's property against this registry at *load* time is what turns
"unknown property path" into a rejected preset rather than a runtime file failure
(spec 11.3.7).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from preflightqc.core.values import MetaField, Provenance

#: Audio presence is derived from stream enumeration rather than read from a field.
_AUDIO_PRESENCE_PROVENANCE = Provenance(
    inspector="computed", field_path="audio.present", derived_from=("streams[]",)
)

# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class InspectorRecord:
    """What one inspector did for one file."""

    name: str
    version: str | None
    ok: bool
    failure_kind: str | None = None
    message: str | None = None
    duration_ms: float | None = None


@dataclass(frozen=True, slots=True)
class ConflictRecord:
    """A field where the two inspectors disagreed."""

    property_path: str
    values: tuple[str, ...]
    inspectors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Diagnostics:
    """Everything the report needs to explain how the metadata was obtained."""

    inspectors: tuple[InspectorRecord, ...] = ()
    conflicts: tuple[ConflictRecord, ...] = ()
    notes: tuple[str, ...] = ()

    def inspector_versions(self) -> Mapping[str, str]:
        return {r.name: (r.version or "unknown") for r in self.inspectors}


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FileInfo:
    """Filesystem-level facts. Spec 9.1."""

    path: Path
    name: str
    size_bytes: MetaField[int]
    duration_seconds: MetaField[float]
    modified_ns: int = 0


@dataclass(frozen=True, slots=True)
class ContainerInfo:
    """Container-level facts. Spec 9.2."""

    #: The set of canonical container tokens the format satisfies; ffprobe reports a
    #: family such as "mov,mp4,m4a", so membership is set intersection.
    formats: MetaField[frozenset[str]]
    format_long_name: MetaField[str]
    major_brand: MetaField[str]
    compatible_brands: MetaField[tuple[str, ...]]
    stream_count: MetaField[int]
    video_stream_count: MetaField[int]
    audio_stream_count: MetaField[int]
    overall_bitrate: MetaField[int]
    faststart: MetaField[bool]
    edit_lists_present: MetaField[bool]
    tags: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VideoStream:
    """One video stream. Spec 9.3."""

    index: int
    codec: MetaField[str]
    profile: MetaField[str]
    level: MetaField[int]
    width: MetaField[int]
    height: MetaField[int]
    coded_width: MetaField[int]
    coded_height: MetaField[int]
    display_width: MetaField[int]
    display_height: MetaField[int]
    sample_aspect_ratio: MetaField[Fraction]
    display_aspect_ratio: MetaField[Fraction]
    rotation_degrees: MetaField[int]
    frame_rate: MetaField[Fraction]
    frame_rate_mode: MetaField[str]
    bitrate: MetaField[int]
    #: "stream" | "container" | "computed" -- reports must not imply a measured value
    #: that was actually derived.
    bitrate_source: MetaField[str]
    pixel_format: MetaField[str]
    bit_depth: MetaField[int]
    chroma_subsampling: MetaField[str]
    scan_type: MetaField[str]
    colour_range: MetaField[str]
    colour_space: MetaField[str]
    transfer_characteristics: MetaField[str]
    colour_primaries: MetaField[str]
    gop_closed: MetaField[bool]
    hdr_format: MetaField[str]
    dolby_vision: MetaField[str]
    max_cll: MetaField[int]
    max_fall: MetaField[int]


@dataclass(frozen=True, slots=True)
class AudioStream:
    """One audio stream. Spec 9.4."""

    index: int
    codec: MetaField[str]
    sample_rate: MetaField[int]
    channels: MetaField[int]
    channel_layout: MetaField[str]
    bitrate: MetaField[int]
    duration_seconds: MetaField[float]


@dataclass(frozen=True, slots=True)
class NormalisedMedia:
    """Everything PreflightQC knows about one file.

    `video[0]` and `audio[0]` are the primary streams. All streams are enumerated, and
    an INFO finding discloses when more than one exists (spec 23).
    """

    file: FileInfo
    container: ContainerInfo
    video: tuple[VideoStream, ...]
    audio: tuple[AudioStream, ...]
    diagnostics: Diagnostics

    @property
    def primary_video(self) -> VideoStream | None:
        return self.video[0] if self.video else None

    @property
    def primary_audio(self) -> AudioStream | None:
        return self.audio[0] if self.audio else None

    @property
    def has_audio(self) -> bool:
        return bool(self.audio)


# ---------------------------------------------------------------------------
# Property path registry
# ---------------------------------------------------------------------------

_ABSENT_NO_VIDEO = "the file has no video stream"
_ABSENT_NO_AUDIO = "the file has no audio stream"


def _video(getter: Callable[[VideoStream], MetaField[Any]]) -> Callable[[NormalisedMedia], MetaField[Any]]:
    def resolve(media: NormalisedMedia) -> MetaField[Any]:
        stream = media.primary_video
        if stream is None:
            return MetaField.undetermined(_ABSENT_NO_VIDEO)
        return getter(stream)

    return resolve


def _audio(getter: Callable[[AudioStream], MetaField[Any]]) -> Callable[[NormalisedMedia], MetaField[Any]]:
    def resolve(media: NormalisedMedia) -> MetaField[Any]:
        stream = media.primary_audio
        if stream is None:
            return MetaField.undetermined(_ABSENT_NO_AUDIO)
        return getter(stream)

    return resolve


@dataclass(frozen=True, slots=True)
class PropertyDescriptor:
    """A property a rule may target, with the metadata a finding needs to explain it."""

    path: str
    label: str
    unit: str | None
    resolve: Callable[[NormalisedMedia], MetaField[Any]]


def _descriptor(
    path: str,
    label: str,
    unit: str | None,
    resolve: Callable[[NormalisedMedia], MetaField[Any]],
) -> tuple[str, PropertyDescriptor]:
    return path, PropertyDescriptor(path=path, label=label, unit=unit, resolve=resolve)


PROPERTY_PATHS: Mapping[str, PropertyDescriptor] = dict(
    (
        # -- file ----------------------------------------------------------
        _descriptor("file.size_bytes", "File size", "bytes", lambda m: m.file.size_bytes),
        _descriptor("file.duration_seconds", "Duration", "s", lambda m: m.file.duration_seconds),
        # -- container -----------------------------------------------------
        _descriptor("container.format", "Container", None, lambda m: m.container.formats),
        _descriptor("container.major_brand", "Major brand", None, lambda m: m.container.major_brand),
        _descriptor("container.stream_count", "Stream count", None, lambda m: m.container.stream_count),
        _descriptor(
            "container.video_stream_count", "Video streams", None, lambda m: m.container.video_stream_count
        ),
        _descriptor(
            "container.audio_stream_count", "Audio streams", None, lambda m: m.container.audio_stream_count
        ),
        _descriptor(
            "container.overall_bitrate", "Overall bitrate", "bit/s", lambda m: m.container.overall_bitrate
        ),
        _descriptor("container.faststart", "Fast start (moov at front)", None, lambda m: m.container.faststart),
        _descriptor(
            "container.edit_lists_present", "Edit lists present", None, lambda m: m.container.edit_lists_present
        ),
        # -- video ---------------------------------------------------------
        _descriptor("video.codec", "Video codec", None, _video(lambda s: s.codec)),
        _descriptor("video.profile", "Video profile", None, _video(lambda s: s.profile)),
        _descriptor("video.level", "Video level", None, _video(lambda s: s.level)),
        _descriptor("video.width", "Width", "px", _video(lambda s: s.width)),
        _descriptor("video.height", "Height", "px", _video(lambda s: s.height)),
        _descriptor("video.coded_width", "Coded width", "px", _video(lambda s: s.coded_width)),
        _descriptor("video.coded_height", "Coded height", "px", _video(lambda s: s.coded_height)),
        _descriptor("video.display_width", "Displayed width", "px", _video(lambda s: s.display_width)),
        _descriptor("video.display_height", "Displayed height", "px", _video(lambda s: s.display_height)),
        _descriptor(
            "video.sample_aspect_ratio", "Sample aspect ratio", None, _video(lambda s: s.sample_aspect_ratio)
        ),
        _descriptor(
            "video.display_aspect_ratio", "Display aspect ratio", None, _video(lambda s: s.display_aspect_ratio)
        ),
        _descriptor("video.rotation_degrees", "Rotation", "deg", _video(lambda s: s.rotation_degrees)),
        _descriptor("video.frame_rate", "Frame rate", "fps", _video(lambda s: s.frame_rate)),
        _descriptor("video.frame_rate_mode", "Frame rate mode", None, _video(lambda s: s.frame_rate_mode)),
        _descriptor("video.bitrate", "Video bitrate", "bit/s", _video(lambda s: s.bitrate)),
        _descriptor("video.pixel_format", "Pixel format", None, _video(lambda s: s.pixel_format)),
        _descriptor("video.bit_depth", "Bit depth", "bit", _video(lambda s: s.bit_depth)),
        _descriptor(
            "video.chroma_subsampling", "Chroma subsampling", None, _video(lambda s: s.chroma_subsampling)
        ),
        _descriptor("video.scan_type", "Scan type", None, _video(lambda s: s.scan_type)),
        _descriptor("video.colour_range", "Colour range", None, _video(lambda s: s.colour_range)),
        _descriptor("video.colour_space", "Colour space", None, _video(lambda s: s.colour_space)),
        _descriptor(
            "video.transfer_characteristics",
            "Transfer characteristics",
            None,
            _video(lambda s: s.transfer_characteristics),
        ),
        _descriptor("video.colour_primaries", "Colour primaries", None, _video(lambda s: s.colour_primaries)),
        _descriptor("video.gop_closed", "Closed GOP", None, _video(lambda s: s.gop_closed)),
        _descriptor("video.hdr_format", "HDR format", None, _video(lambda s: s.hdr_format)),
        _descriptor("video.dolby_vision", "Dolby Vision", None, _video(lambda s: s.dolby_vision)),
        _descriptor("video.max_cll", "MaxCLL", "cd/m2", _video(lambda s: s.max_cll)),
        _descriptor("video.max_fall", "MaxFALL", "cd/m2", _video(lambda s: s.max_fall)),
        # -- audio ---------------------------------------------------------
        _descriptor(
            "audio.present",
            "Audio present",
            None,
            lambda m: MetaField.known(True, _AUDIO_PRESENCE_PROVENANCE)
            if m.has_audio
            else MetaField.known(False, _AUDIO_PRESENCE_PROVENANCE),
        ),
        _descriptor("audio.codec", "Audio codec", None, _audio(lambda s: s.codec)),
        _descriptor("audio.sample_rate", "Audio sample rate", "Hz", _audio(lambda s: s.sample_rate)),
        _descriptor("audio.channels", "Audio channels", None, _audio(lambda s: s.channels)),
        _descriptor("audio.channel_layout", "Audio channel layout", None, _audio(lambda s: s.channel_layout)),
        _descriptor("audio.bitrate", "Audio bitrate", "bit/s", _audio(lambda s: s.bitrate)),
        _descriptor(
            "audio.duration_seconds", "Audio duration", "s", _audio(lambda s: s.duration_seconds)
        ),
    )
)

def resolve_property(media: NormalisedMedia, path: str) -> MetaField[Any]:
    """Resolve a canonical property path against a normalised model.

    Raises KeyError for an unknown path. The preset loader checks every path up front,
    so this should be unreachable at evaluation time.
    """
    return PROPERTY_PATHS[path].resolve(media)


def is_known_property(path: str) -> bool:
    return path in PROPERTY_PATHS
