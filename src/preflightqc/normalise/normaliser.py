"""Raw inspector intermediates to the normalised metadata model.

The rules this module enforces (spec 9.6, ARCHITECTURE-V1.md section 5.3):

1. Missing is not zero. An absent bitrate is NOT_PRESENT, never 0.
2. Undetermined is not missing. A value the inspector reported as "unknown" is
   UNDETERMINED, which is a different fact and is reported differently.
3. Every field carries provenance naming the inspector and the raw field path.
4. Derived values are flagged derived.
5. Disagreement between inspectors is preserved as CONFLICTED, never averaged.
6. An unmapped vocabulary token becomes UNDETERMINED with the raw string retained --
   never coerced to a plausible-looking default.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, TypeVar

from preflightqc.adapters.base import RawInspection, RawStream
from preflightqc.core import vocabulary as vocab
from preflightqc.core.geometry import (
    compute_display_geometry,
    normalise_rotation,
    parse_rational,
)
from preflightqc.core.model import (
    AudioStream,
    ConflictRecord,
    ContainerInfo,
    Diagnostics,
    FileInfo,
    InspectorRecord,
    NormalisedMedia,
    VideoStream,
)
from preflightqc.core.values import MetaField, Provenance, computed
from preflightqc.normalise import precedence

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Observation:
    """One inspector's reading of one property."""

    value: Any
    provenance: Provenance


def _observe(
    inspector: str,
    field_path: str,
    raw: Any,
    convert: Callable[[Any], T | None],
    *,
    tool_version: str | None = None,
) -> Observation | None:
    """Convert a raw inspector value into an Observation, or None if unusable.

    `convert` returning None means "this inspector gave us nothing usable here", which
    is deliberately indistinguishable from the field being absent: both leave the
    property with no observation, and the combiner decides what that means.
    """
    if raw is None:
        return None
    value = convert(raw)
    if value is None:
        return None
    return Observation(
        value=value,
        provenance=Provenance(inspector=inspector, field_path=field_path, tool_version=tool_version),
    )


def _numeric_agreement(left: Any, right: Any, *, is_duration: bool = False) -> bool:
    """Whether two numeric observations are close enough to count as agreement."""
    try:
        a, b = float(left), float(right)
    except (TypeError, ValueError):
        return bool(left == right)
    if is_duration and abs(a - b) <= precedence.DURATION_AGREEMENT_SECONDS:
        return True
    scale = max(abs(a), abs(b))
    if scale == 0.0:
        return True
    return abs(a - b) / scale <= precedence.NUMERIC_AGREEMENT_TOLERANCE


def _combine(
    property_path: str,
    observations: list[Observation | None],
    *,
    numeric: bool = False,
    is_duration: bool = False,
    absent_reason: str | None = None,
    conflicts_out: list[ConflictRecord] | None = None,
) -> MetaField[Any]:
    """Fold per-inspector observations into a single MetaField.

    - No observation at all -> UNDETERMINED (or NOT_PRESENT when the caller knows the
      property is genuinely absent rather than merely unread).
    - One observation -> KNOWN.
    - Two that agree -> KNOWN, from the precedence winner.
    - Two that disagree -> CONFLICTED, both preserved.
    """
    present = [obs for obs in observations if obs is not None]
    if not present:
        return MetaField.undetermined(
            absent_reason or "no inspector reported this property"
        )

    present.sort(key=lambda obs: precedence.prefers(property_path, obs.provenance.inspector))
    winner = present[0]

    if len(present) > 1:
        others = present[1:]
        disagreeing = [
            obs
            for obs in others
            if not (
                _numeric_agreement(winner.value, obs.value, is_duration=is_duration)
                if numeric
                else vocab.values_agree(property_path, winner.value, obs.value)
            )
        ]
        if disagreeing:
            observations_pairs = tuple(
                (obs.value, obs.provenance) for obs in (winner, *disagreeing)
            )
            if conflicts_out is not None:
                conflicts_out.append(
                    ConflictRecord(
                        property_path=property_path,
                        values=tuple(str(v) for v, _ in observations_pairs),
                        inspectors=tuple(p.inspector for _, p in observations_pairs),
                    )
                )
            return MetaField.conflicted(*observations_pairs)

    return MetaField.known(winner.value, winner.provenance)


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------


def _to_int(raw: Any) -> int | None:
    try:
        value = int(float(str(raw).strip()))
    except (TypeError, ValueError):
        return None
    return value


def _to_positive_int(raw: Any) -> int | None:
    value = _to_int(raw)
    return value if value is not None and value > 0 else None


def _to_float(raw: Any) -> float | None:
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        return None


def _to_positive_float(raw: Any) -> float | None:
    value = _to_float(raw)
    return value if value is not None and value > 0 else None


def _ms_to_seconds(raw: Any) -> float | None:
    """MediaInfo emits durations in seconds as a string in JSON output."""
    return _to_positive_float(raw)


def _to_str(raw: Any) -> str | None:
    text = str(raw).strip()
    return text or None


def _to_bool(raw: Any) -> bool | None:
    if isinstance(raw, bool):
        return raw
    text = str(raw).strip().lower()
    if text in {"yes", "true", "1"}:
        return True
    if text in {"no", "false", "0"}:
        return False
    return None


# ---------------------------------------------------------------------------
# Section normalisers
# ---------------------------------------------------------------------------


def _normalise_container(
    ff: RawInspection | None,
    mi: RawInspection | None,
    conflicts: list[ConflictRecord],
) -> ContainerInfo:
    ff_c = ff.container if ff else {}
    mi_c = mi.container if mi else {}

    def formats_from_ffprobe(raw: Any) -> frozenset[str] | None:
        tokens = vocab.canonical_containers(str(raw))
        return tokens or None

    def formats_from_mediainfo(raw: Any) -> frozenset[str] | None:
        tokens = vocab.canonical_containers(str(raw))
        return tokens or None

    formats_obs = [
        _observe("ffprobe", "format.format_name", ff_c.get("format_name"), formats_from_ffprobe),
        _observe("mediainfo", "General.Format", mi_c.get("Format"), formats_from_mediainfo),
    ]
    formats = _combine("container.format", formats_obs, conflicts_out=conflicts)
    # An unmapped container string must not silently become "no match"; retain the raw
    # value so a report can show what was actually seen.
    if formats.is_undetermined and ff_c.get("format_name"):
        formats = MetaField.undetermined(
            "container format not recognised by PreflightQC",
            raw=str(ff_c.get("format_name")),
        )

    video_count = _combine(
        "container.video_stream_count",
        [
            _observe(
                "ffprobe",
                "streams[video]",
                len(ff.streams_of("video")) if ff else None,
                _to_int,
            ),
            _observe("mediainfo", "General.VideoCount", mi_c.get("VideoCount"), _to_int),
        ],
        numeric=True,
    )
    audio_count = _combine(
        "container.audio_stream_count",
        [
            _observe(
                "ffprobe",
                "streams[audio]",
                len(ff.streams_of("audio")) if ff else None,
                _to_int,
            ),
            _observe("mediainfo", "General.AudioCount", mi_c.get("AudioCount"), _to_int),
        ],
        numeric=True,
    )

    return ContainerInfo(
        formats=formats,
        format_long_name=_combine(
            "container.format_long_name",
            [_observe("ffprobe", "format.format_long_name", ff_c.get("format_long_name"), _to_str)],
        ),
        major_brand=_combine(
            "container.major_brand",
            [
                _observe("ffprobe", "format.tags.major_brand", ff_c.get("major_brand"), _to_str),
                _observe("mediainfo", "General.CodecID", mi_c.get("CodecID"), _to_str),
            ],
            conflicts_out=conflicts,
        ),
        compatible_brands=_combine(
            "container.compatible_brands",
            [
                _observe(
                    "ffprobe",
                    "format.tags.compatible_brands",
                    ff_c.get("compatible_brands"),
                    lambda raw: tuple(str(raw)[i : i + 4] for i in range(0, len(str(raw)), 4)) or None,
                )
            ],
        ),
        stream_count=_combine(
            "container.stream_count",
            [_observe("ffprobe", "format.nb_streams", ff_c.get("nb_streams"), _to_int)],
            numeric=True,
        ),
        video_stream_count=video_count,
        audio_stream_count=audio_count,
        overall_bitrate=_combine(
            "container.overall_bitrate",
            [
                _observe("ffprobe", "format.bit_rate", ff_c.get("bit_rate"), _to_positive_int),
                _observe("mediainfo", "General.OverallBitRate", mi_c.get("OverallBitRate"), _to_positive_int),
            ],
            numeric=True,
            conflicts_out=conflicts,
        ),
        # Register gap G-1/faststart: ffprobe exposes no direct field, so when MediaInfo
        # is unavailable this stays UNDETERMINED rather than being guessed.
        faststart=_combine(
            "container.faststart",
            [_observe("mediainfo", "General.IsStreamable", mi_c.get("IsStreamable"), _to_bool)],
            absent_reason=(
                "fast-start position requires atom-level inspection; "
                "not determined by PreflightQC V1"
            ),
        ),
        # Register gap G-1: edit-list presence needs atom-level inspection. Neither
        # inspector exposes it directly, so it is honestly undetermined.
        edit_lists_present=MetaField.undetermined(
            "edit-list presence requires atom-level inspection; not determined by PreflightQC V1"
        ),
        tags=dict(ff_c.get("tags") or {}),
    )


def _normalise_video(
    index: int,
    ff_stream: RawStream | None,
    mi_stream: RawStream | None,
    container_bitrate: MetaField[int],
    duration: MetaField[float],
    conflicts: list[ConflictRecord],
) -> VideoStream:
    ffs = ff_stream.fields if ff_stream else {}
    mis = mi_stream.fields if mi_stream else {}

    codec = _combine(
        "video.codec",
        [
            _observe("ffprobe", "streams[].codec_name", ffs.get("codec_name"), vocab.canonical_video_codec),
            _observe("mediainfo", "Video.Format", mis.get("Format"), vocab.canonical_video_codec),
        ],
        conflicts_out=conflicts,
    )
    if codec.is_undetermined and ffs.get("codec_name"):
        codec = MetaField.undetermined(
            "video codec not recognised by PreflightQC", raw=str(ffs.get("codec_name"))
        )

    width = _combine(
        "video.width",
        [
            _observe("ffprobe", "streams[].width", ffs.get("width"), _to_positive_int),
            _observe("mediainfo", "Video.Width", mis.get("Width"), _to_positive_int),
        ],
        numeric=True,
        conflicts_out=conflicts,
    )
    height = _combine(
        "video.height",
        [
            _observe("ffprobe", "streams[].height", ffs.get("height"), _to_positive_int),
            _observe("mediainfo", "Video.Height", mis.get("Height"), _to_positive_int),
        ],
        numeric=True,
        conflicts_out=conflicts,
    )

    sar = _combine(
        "video.sample_aspect_ratio",
        [
            _observe(
                "ffprobe",
                "streams[].sample_aspect_ratio",
                ffs.get("sample_aspect_ratio"),
                lambda raw: parse_rational(str(raw)),
            ),
            _observe(
                "mediainfo",
                "Video.PixelAspectRatio",
                mis.get("PixelAspectRatio"),
                lambda raw: parse_rational(str(raw)),
            ),
        ],
        numeric=True,
        conflicts_out=conflicts,
    )

    rotation_raw = ffs.get("rotation")
    if rotation_raw is None:
        rotation_raw = mis.get("Rotation")
    rotation = _combine(
        "video.rotation_degrees",
        [
            _observe(
                "ffprobe" if ffs.get("rotation") is not None else "mediainfo",
                "side_data[Display Matrix].rotation",
                rotation_raw,
                lambda raw: normalise_rotation(float(raw)) if _to_float(raw) is not None else None,
            )
        ],
    )
    # No rotation metadata means no rotation. That is a fact about the file, not a gap.
    if rotation.is_undetermined:
        rotation = MetaField.known(
            0, computed("video.rotation_degrees", derived_from=("absence of rotation metadata",))
        )

    # Displayed geometry: SAR and rotation applied. Aspect-ratio rules evaluate here,
    # never against raw width/height.
    display_width: MetaField[int] = MetaField.undetermined("coded dimensions unavailable")
    display_height: MetaField[int] = MetaField.undetermined("coded dimensions unavailable")
    dar: MetaField[Fraction] = MetaField.undetermined("coded dimensions unavailable")
    if width.is_known and height.is_known:
        geometry = compute_display_geometry(
            width.value,
            height.value,
            sample_aspect_ratio=sar.or_none(),
            rotation_degrees=rotation.unwrap_or(0),
        )
        derived_from = ("video.width", "video.height", "video.sample_aspect_ratio", "video.rotation_degrees")
        display_width = MetaField.known(
            geometry.display_width, computed("video.display_width", derived_from=derived_from)
        )
        display_height = MetaField.known(
            geometry.display_height, computed("video.display_height", derived_from=derived_from)
        )
        dar = MetaField.known(
            geometry.display_aspect_ratio, computed("video.display_aspect_ratio", derived_from=derived_from)
        )

    frame_rate = _combine(
        "video.frame_rate",
        [
            _observe(
                "ffprobe",
                "streams[].avg_frame_rate",
                ffs.get("avg_frame_rate") or ffs.get("r_frame_rate"),
                lambda raw: parse_rational(str(raw)),
            ),
            _observe(
                "mediainfo", "Video.FrameRate", mis.get("FrameRate"), lambda raw: parse_rational(str(raw))
            ),
        ],
        numeric=True,
        conflicts_out=conflicts,
    )

    # Register gap G-5: a single field is often insufficient for VFR detection. When
    # MediaInfo does not signal it, this stays UNDETERMINED so that a "must be constant"
    # rule yields UNKNOWN rather than a wrong FAIL.
    frame_rate_mode = _combine(
        "video.frame_rate_mode",
        [
            _observe(
                "mediainfo",
                "Video.FrameRate_Mode",
                mis.get("FrameRate_Mode"),
                vocab.canonical_frame_rate_mode,
            )
        ],
        absent_reason="frame-rate mode is not signalled by the container",
    )

    # Bitrate: prefer the stream-level value, fall back to container, then to a
    # computation. The source is recorded so a report never implies a measured value
    # that was actually derived.
    bitrate = _combine(
        "video.bitrate",
        [
            _observe("ffprobe", "streams[].bit_rate", ffs.get("bit_rate"), _to_positive_int),
            _observe("mediainfo", "Video.BitRate", mis.get("BitRate"), _to_positive_int),
        ],
        numeric=True,
        conflicts_out=conflicts,
    )
    bitrate_source: MetaField[str] = MetaField.known(
        "stream", computed("video.bitrate_source", derived_from=("streams[].bit_rate",))
    )
    if bitrate.is_absent and container_bitrate.is_known:
        bitrate = MetaField.known(
            container_bitrate.value,
            computed("video.bitrate", derived_from=("container.overall_bitrate",)),
        )
        bitrate_source = MetaField.known(
            "container", computed("video.bitrate_source", derived_from=("container.overall_bitrate",))
        )

    pixel_format = _combine(
        "video.pixel_format", [_observe("ffprobe", "streams[].pix_fmt", ffs.get("pix_fmt"), _to_str)]
    )

    chroma_obs: list[Observation | None] = [
        _observe(
            "ffprobe",
            "streams[].pix_fmt",
            ffs.get("pix_fmt"),
            lambda raw: (facts.chroma_subsampling if (facts := vocab.pixel_format_facts(str(raw))) else None),
        ),
        _observe(
            "mediainfo", "Video.ChromaSubsampling", mis.get("ChromaSubsampling"), vocab.canonical_chroma
        ),
    ]
    chroma = _combine("video.chroma_subsampling", chroma_obs, conflicts_out=conflicts)
    if chroma.is_undetermined and ffs.get("pix_fmt"):
        chroma = MetaField.undetermined(
            "pixel format not recognised by PreflightQC", raw=str(ffs.get("pix_fmt"))
        )

    bit_depth = _combine(
        "video.bit_depth",
        [
            _observe(
                "ffprobe",
                "streams[].bits_per_raw_sample",
                ffs.get("bits_per_raw_sample"),
                _to_positive_int,
            ),
            _observe(
                "ffprobe",
                "streams[].pix_fmt",
                ffs.get("pix_fmt"),
                lambda raw: (facts.bit_depth if (facts := vocab.pixel_format_facts(str(raw))) else None),
            ),
            _observe("mediainfo", "Video.BitDepth", mis.get("BitDepth"), _to_positive_int),
        ],
        numeric=True,
    )

    # Register gap G-3: both inspectors are heuristic here. A FAIL on scan type is only
    # ever emitted when interlacing is positively reported; anything else is UNDETERMINED.
    scan_type = _combine(
        "video.scan_type",
        [
            _observe("mediainfo", "Video.ScanType", mis.get("ScanType"), vocab.canonical_scan_type),
            _observe("ffprobe", "streams[].field_order", ffs.get("field_order"), vocab.canonical_scan_type),
        ],
        absent_reason="scan type is not signalled by the container (inspectors report it heuristically)",
        conflicts_out=conflicts,
    )

    def colour(path: str, ff_key: str, mi_key: str, convert: Callable[[Any], str | None]) -> MetaField[str]:
        ff_raw = ffs.get(ff_key)
        if isinstance(ff_raw, str) and vocab.is_colour_absent(ff_raw):
            ff_raw = None
        return _combine(
            path,
            [
                _observe("ffprobe", f"streams[].{ff_key}", ff_raw, convert),
                _observe("mediainfo", f"Video.{mi_key}", mis.get(mi_key), convert),
            ],
            absent_reason="the stream carries no colour description",
            conflicts_out=conflicts,
        )

    hdr_format = _combine(
        "video.hdr_format",
        [
            _observe("mediainfo", "Video.HDR_Format", mis.get("HDR_Format"), _to_str),
            _observe(
                "ffprobe",
                "side_data[Mastering display metadata]",
                "SMPTE ST 2086" if ffs.get("mastering_display") else None,
                _to_str,
            ),
        ],
        absent_reason="no HDR metadata found",
    )

    dolby_vision = _combine(
        "video.dolby_vision",
        [
            _observe("mediainfo", "Video.HDR_Format_Profile", mis.get("HDR_Format_Profile"), _to_str),
            _observe("ffprobe", "side_data[DOVI]", ffs.get("dolby_vision"), _to_str),
        ],
        absent_reason=(
            "no Dolby Vision metadata found (note: DV in raw HEVC is a documented "
            "inspector limitation)"
        ),
    )

    return VideoStream(
        index=index,
        codec=codec,
        profile=_combine(
            "video.profile",
            [
                _observe("ffprobe", "streams[].profile", ffs.get("profile"), _to_str),
                _observe("mediainfo", "Video.Format_Profile", mis.get("Format_Profile"), _to_str),
            ],
            conflicts_out=conflicts,
        ),
        level=_combine("video.level", [_observe("ffprobe", "streams[].level", ffs.get("level"), _to_int)]),
        width=width,
        height=height,
        coded_width=_combine(
            "video.coded_width",
            [_observe("ffprobe", "streams[].coded_width", ffs.get("coded_width"), _to_positive_int)],
        ),
        coded_height=_combine(
            "video.coded_height",
            [_observe("ffprobe", "streams[].coded_height", ffs.get("coded_height"), _to_positive_int)],
        ),
        display_width=display_width,
        display_height=display_height,
        sample_aspect_ratio=sar,
        display_aspect_ratio=dar,
        rotation_degrees=rotation,
        frame_rate=frame_rate,
        frame_rate_mode=frame_rate_mode,
        bitrate=bitrate,
        bitrate_source=bitrate_source,
        pixel_format=pixel_format,
        bit_depth=bit_depth,
        chroma_subsampling=chroma,
        scan_type=scan_type,
        colour_range=colour("video.colour_range", "color_range", "colour_range", vocab.canonical_colour_range),
        colour_space=colour("video.colour_space", "color_space", "matrix_coefficients", _to_str),
        transfer_characteristics=colour(
            "video.transfer_characteristics",
            "color_transfer",
            "transfer_characteristics",
            vocab.canonical_transfer,
        ),
        colour_primaries=colour(
            "video.colour_primaries", "color_primaries", "colour_primaries", vocab.canonical_primaries
        ),
        # Register gap G-2: closed-GOP verification needs packet-level analysis, which is
        # beyond the V1 inspection cost boundary (spec 10.5).
        gop_closed=MetaField.undetermined(
            "closed-GOP verification requires packet-level analysis; not measured by PreflightQC V1"
        ),
        hdr_format=hdr_format,
        dolby_vision=dolby_vision,
        max_cll=_combine(
            "video.max_cll",
            [
                _observe("mediainfo", "Video.MaxCLL", mis.get("MaxCLL"), _to_positive_int),
                _observe("ffprobe", "side_data[CLL].max_content", ffs.get("max_cll"), _to_positive_int),
            ],
            numeric=True,
        ),
        max_fall=_combine(
            "video.max_fall",
            [
                _observe("mediainfo", "Video.MaxFALL", mis.get("MaxFALL"), _to_positive_int),
                _observe("ffprobe", "side_data[CLL].max_average", ffs.get("max_fall"), _to_positive_int),
            ],
            numeric=True,
        ),
    )


def _normalise_audio(
    index: int,
    ff_stream: RawStream | None,
    mi_stream: RawStream | None,
    conflicts: list[ConflictRecord],
) -> AudioStream:
    ffs = ff_stream.fields if ff_stream else {}
    mis = mi_stream.fields if mi_stream else {}

    codec = _combine(
        "audio.codec",
        [
            _observe("ffprobe", "streams[].codec_name", ffs.get("codec_name"), vocab.canonical_audio_codec),
            _observe("mediainfo", "Audio.Format", mis.get("Format"), vocab.canonical_audio_codec),
        ],
        conflicts_out=conflicts,
    )
    if codec.is_undetermined and ffs.get("codec_name"):
        codec = MetaField.undetermined(
            "audio codec not recognised by PreflightQC", raw=str(ffs.get("codec_name"))
        )

    return AudioStream(
        index=index,
        codec=codec,
        sample_rate=_combine(
            "audio.sample_rate",
            [
                _observe("ffprobe", "streams[].sample_rate", ffs.get("sample_rate"), _to_positive_int),
                _observe("mediainfo", "Audio.SamplingRate", mis.get("SamplingRate"), _to_positive_int),
            ],
            numeric=True,
            conflicts_out=conflicts,
        ),
        channels=_combine(
            "audio.channels",
            [
                _observe("ffprobe", "streams[].channels", ffs.get("channels"), _to_positive_int),
                _observe("mediainfo", "Audio.Channels", mis.get("Channels"), _to_positive_int),
            ],
            numeric=True,
            conflicts_out=conflicts,
        ),
        channel_layout=_combine(
            "audio.channel_layout",
            [
                _observe("ffprobe", "streams[].channel_layout", ffs.get("channel_layout"), _to_str),
                _observe("mediainfo", "Audio.ChannelLayout", mis.get("ChannelLayout"), _to_str),
            ],
            conflicts_out=conflicts,
        ),
        bitrate=_combine(
            "audio.bitrate",
            [
                _observe("ffprobe", "streams[].bit_rate", ffs.get("bit_rate"), _to_positive_int),
                _observe("mediainfo", "Audio.BitRate", mis.get("BitRate"), _to_positive_int),
            ],
            numeric=True,
            conflicts_out=conflicts,
        ),
        duration_seconds=_combine(
            "audio.duration_seconds",
            [
                _observe("ffprobe", "streams[].duration", ffs.get("duration"), _to_positive_float),
                _observe("mediainfo", "Audio.Duration", mis.get("Duration"), _ms_to_seconds),
            ],
            numeric=True,
            is_duration=True,
        ),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def normalise(
    path: Path,
    *,
    ffprobe: RawInspection | None,
    mediainfo: RawInspection | None,
    size_bytes: int | None = None,
    modified_ns: int = 0,
    inspector_records: tuple[InspectorRecord, ...] = (),
    notes: tuple[str, ...] = (),
) -> NormalisedMedia:
    """Build the normalised model from whatever the inspectors managed to produce.

    Either inspector may be None -- that is the documented behaviour when one crashes
    (spec 23). The model simply carries more UNDETERMINED fields, which the engine turns
    into UNKNOWN findings rather than failures.
    """
    conflicts: list[ConflictRecord] = []

    container = _normalise_container(ffprobe, mediainfo, conflicts)

    ff_c = ffprobe.container if ffprobe else {}
    mi_c = mediainfo.container if mediainfo else {}

    duration = _combine(
        "file.duration_seconds",
        [
            _observe("ffprobe", "format.duration", ff_c.get("duration"), _to_positive_float),
            _observe("mediainfo", "General.Duration", mi_c.get("Duration"), _ms_to_seconds),
        ],
        numeric=True,
        is_duration=True,
        conflicts_out=conflicts,
    )

    # File size comes from the filesystem when we have it: it is ground truth, and both
    # inspectors merely echo it.
    if size_bytes is not None:
        size = MetaField.known(
            size_bytes,
            Provenance(inspector="filesystem", field_path="stat.st_size"),
        )
    else:
        size = _combine(
            "file.size_bytes",
            [
                _observe("ffprobe", "format.size", ff_c.get("size"), _to_positive_int),
                _observe("mediainfo", "General.FileSize", mi_c.get("FileSize"), _to_positive_int),
            ],
            numeric=True,
        )

    ff_videos = ffprobe.streams_of("video") if ffprobe else ()
    mi_videos = mediainfo.streams_of("video") if mediainfo else ()
    ff_audios = ffprobe.streams_of("audio") if ffprobe else ()
    mi_audios = mediainfo.streams_of("audio") if mediainfo else ()

    video_streams = tuple(
        _normalise_video(
            index,
            ff_videos[index] if index < len(ff_videos) else None,
            mi_videos[index] if index < len(mi_videos) else None,
            container.overall_bitrate,
            duration,
            conflicts,
        )
        for index in range(max(len(ff_videos), len(mi_videos)))
    )
    audio_streams = tuple(
        _normalise_audio(
            index,
            ff_audios[index] if index < len(ff_audios) else None,
            mi_audios[index] if index < len(mi_audios) else None,
            conflicts,
        )
        for index in range(max(len(ff_audios), len(mi_audios)))
    )

    extra_notes = list(notes)
    if len(video_streams) > 1:
        extra_notes.append(
            f"{len(video_streams)} video streams found; stream 0 was validated as primary"
        )
    if len(audio_streams) > 1:
        extra_notes.append(
            f"{len(audio_streams)} audio streams found; stream 0 was validated as primary"
        )

    return NormalisedMedia(
        file=FileInfo(
            path=path,
            name=path.name,
            size_bytes=size,
            duration_seconds=duration,
            modified_ns=modified_ns,
        ),
        container=container,
        video=video_streams,
        audio=audio_streams,
        diagnostics=Diagnostics(
            inspectors=inspector_records,
            conflicts=tuple(conflicts),
            notes=tuple(extra_notes),
        ),
    )
