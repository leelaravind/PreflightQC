"""Canonicalisation tables.

Inspectors report the same concept under many spellings. The rule engine compares
against canonical tokens, so every raw string passes through one of these tables.

The governing rule: **an unmapped input is never coerced.** It resolves to a miss, and
the caller turns that into `MetaField.undetermined(...)` retaining the raw string. A
silent default here would let a rule compare against a value the file never carried.

All tables are data. Adding a codec or container is a table edit, not a code change.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Containers
# ---------------------------------------------------------------------------

#: Canonical container tokens used by preset rules.
#: ffprobe reports `format_name` as a comma-separated family (e.g. "mov,mp4,m4a,3gp"),
#: so membership matching is by set intersection, not string equality.
_CONTAINER_ALIASES: dict[str, str] = {
    "mp4": "mp4",
    "m4v": "mp4",
    "m4a": "mp4",
    "isom": "mp4",
    "mp42": "mp4",
    "mp41": "mp4",
    "mov": "mov",
    "qt": "mov",
    "quicktime": "mov",
    "matroska": "mkv",
    "mkv": "mkv",
    "webm": "webm",
    "avi": "avi",
    "asf": "asf",
    "wmv": "wmv",
    "wmv2": "wmv",
    "wmv3": "wmv",
    "flv": "flv",
    "mpeg": "mpeg",
    "mpegvideo": "mpeg",
    "mpeg-1": "mpeg1",
    "mpeg1video": "mpeg1",
    "mpeg-2": "mpeg2",
    "mpeg2video": "mpeg2",
    "mpegps": "mpegps",
    "mpegts": "mpegts",
    "3gp": "3gp",
    "3g2": "3gp",
    "3gpp": "3gp",
    "ogg": "ogg",
    "mp3": "mp3",
    "gif": "gif",
}


def canonical_containers(raw: str) -> frozenset[str]:
    """Map a raw container/format string to the set of canonical tokens it satisfies.

    ffprobe's "mov,mp4,m4a,3gp,3g2,mj2" becomes {"mov", "mp4", "3gp"}. An unmapped
    component contributes nothing; an entirely unmapped string yields an empty set,
    which the caller must treat as undetermined rather than as "no match".
    """
    tokens = (part.strip().lower() for part in raw.replace(";", ",").split(","))
    return frozenset(
        _CONTAINER_ALIASES[token] for token in tokens if token and token in _CONTAINER_ALIASES
    )


# ---------------------------------------------------------------------------
# Video codecs
# ---------------------------------------------------------------------------

_VIDEO_CODEC_ALIASES: dict[str, str] = {
    "h264": "h264",
    "avc": "h264",
    "avc1": "h264",
    "x264": "h264",
    "h.264": "h264",
    "hevc": "hevc",
    "h265": "hevc",
    "h.265": "hevc",
    "hvc1": "hevc",
    "hev1": "hevc",
    "vp8": "vp8",
    "vp9": "vp9",
    "vp09": "vp9",
    "av1": "av1",
    "av01": "av1",
    "prores": "prores",
    "apch": "prores",
    "apcn": "prores",
    "apcs": "prores",
    "apco": "prores",
    "ap4h": "prores",
    "ap4x": "prores",
    "dnxhd": "dnxhd",
    "dnxhr": "dnxhr",
    "cfhd": "cineform",
    "cineform": "cineform",
    "mpeg1video": "mpeg1video",
    "mpeg2video": "mpeg2video",
    "mpeg4": "mpeg4",
    "msmpeg4v3": "mpeg4",
    "wmv1": "wmv1",
    "wmv2": "wmv2",
    "wmv3": "wmv3",
    "vc1": "vc1",
    "theora": "theora",
    "flv1": "flv1",
}


def canonical_video_codec(raw: str) -> str | None:
    """Canonical video codec token, or None if the input is unmapped."""
    return _VIDEO_CODEC_ALIASES.get(raw.strip().lower())


# ---------------------------------------------------------------------------
# Audio codecs
# ---------------------------------------------------------------------------

_AUDIO_CODEC_ALIASES: dict[str, str] = {
    "aac": "aac",
    "aac_lc": "aac",
    "aac-lc": "aac",
    "mp4a": "aac",
    "mp4a-40-2": "aac",
    "opus": "opus",
    "vorbis": "vorbis",
    "mp3": "mp3",
    "mp2": "mp2",
    "ac3": "ac3",
    "eac3": "eac3",
    "flac": "flac",
    "alac": "alac",
    "pcm_s16le": "pcm",
    "pcm_s24le": "pcm",
    "pcm_s32le": "pcm",
    "pcm_f32le": "pcm",
    "pcm": "pcm",
    "wmav2": "wma",
    "wmapro": "wma",
    "dts": "dts",
    "truehd": "truehd",
}


def canonical_audio_codec(raw: str) -> str | None:
    """Canonical audio codec token, or None if the input is unmapped."""
    return _AUDIO_CODEC_ALIASES.get(raw.strip().lower())


# ---------------------------------------------------------------------------
# Pixel formats -> chroma subsampling + bit depth
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PixelFormatFacts:
    """What a pixel format tells us about chroma subsampling and bit depth."""

    chroma_subsampling: str
    bit_depth: int


_PIXEL_FORMATS: dict[str, PixelFormatFacts] = {
    "yuv420p": PixelFormatFacts("4:2:0", 8),
    "yuvj420p": PixelFormatFacts("4:2:0", 8),
    "nv12": PixelFormatFacts("4:2:0", 8),
    "nv21": PixelFormatFacts("4:2:0", 8),
    "yuv420p10le": PixelFormatFacts("4:2:0", 10),
    "yuv420p10be": PixelFormatFacts("4:2:0", 10),
    "p010le": PixelFormatFacts("4:2:0", 10),
    "yuv420p12le": PixelFormatFacts("4:2:0", 12),
    "yuv422p": PixelFormatFacts("4:2:2", 8),
    "yuvj422p": PixelFormatFacts("4:2:2", 8),
    "nv16": PixelFormatFacts("4:2:2", 8),
    "yuv422p10le": PixelFormatFacts("4:2:2", 10),
    "yuv422p10be": PixelFormatFacts("4:2:2", 10),
    "p210le": PixelFormatFacts("4:2:2", 10),
    "yuv422p12le": PixelFormatFacts("4:2:2", 12),
    "yuv444p": PixelFormatFacts("4:4:4", 8),
    "yuvj444p": PixelFormatFacts("4:4:4", 8),
    "yuv444p10le": PixelFormatFacts("4:4:4", 10),
    "yuv444p12le": PixelFormatFacts("4:4:4", 12),
    "yuva444p10le": PixelFormatFacts("4:4:4", 10),
    "gbrp": PixelFormatFacts("4:4:4", 8),
    "gbrp10le": PixelFormatFacts("4:4:4", 10),
    "gbrp12le": PixelFormatFacts("4:4:4", 12),
    "rgb24": PixelFormatFacts("4:4:4", 8),
    "bgr24": PixelFormatFacts("4:4:4", 8),
    "rgba": PixelFormatFacts("4:4:4", 8),
    "bgra": PixelFormatFacts("4:4:4", 8),
}


def pixel_format_facts(raw: str) -> PixelFormatFacts | None:
    """Chroma subsampling and bit depth for a pixel format, or None if unmapped.

    An unmapped format must become UNDETERMINED with the raw string retained. Guessing
    "probably 4:2:0" here would silently manufacture the evidence for a FAIL.
    """
    return _PIXEL_FORMATS.get(raw.strip().lower())


#: MediaInfo reports chroma subsampling directly; normalise its spelling.
def canonical_chroma(raw: str) -> str | None:
    token = raw.strip().lower().replace(" ", "")
    return token if token in {"4:2:0", "4:2:2", "4:4:4", "4:1:1", "4:0:0"} else None


# ---------------------------------------------------------------------------
# Scan type
# ---------------------------------------------------------------------------

_SCAN_TYPES: dict[str, str] = {
    "progressive": "progressive",
    "prog": "progressive",
    "tt": "interlaced",
    "bb": "interlaced",
    "tb": "interlaced",
    "bt": "interlaced",
    "interlaced": "interlaced",
    "mbaff": "interlaced",
    "paff": "interlaced",
    "toplevelfirst": "interlaced",
    "top field first": "interlaced",
    "bottom field first": "interlaced",
}

#: Values that positively mean "the inspector does not know", as opposed to a value we
#: failed to map. Both become UNDETERMINED, but only these are expected.
SCAN_TYPE_UNKNOWN_TOKENS = frozenset({"unknown", "unspecified", "", "n/a"})


def canonical_scan_type(raw: str) -> str | None:
    """"progressive" / "interlaced", or None when unmapped or explicitly unknown.

    ffprobe frequently reports `field_order: unknown` (register gap G-3), and MediaInfo
    reads container flags rather than pixels. Both are advisory, so a FAIL on scan type
    is only ever emitted when interlacing is *positively* reported.
    """
    token = raw.strip().lower()
    if token in SCAN_TYPE_UNKNOWN_TOKENS:
        return None
    return _SCAN_TYPES.get(token)


# ---------------------------------------------------------------------------
# Frame-rate mode
# ---------------------------------------------------------------------------

_FRAME_RATE_MODES: dict[str, str] = {
    "cfr": "CFR",
    "constant": "CFR",
    "vfr": "VFR",
    "variable": "VFR",
}


def canonical_frame_rate_mode(raw: str) -> str | None:
    return _FRAME_RATE_MODES.get(raw.strip().lower())


# ---------------------------------------------------------------------------
# Colour / HDR
# ---------------------------------------------------------------------------

_TRANSFER_CHARACTERISTICS: dict[str, str] = {
    "bt709": "bt709",
    "bt.709": "bt709",
    "smpte170m": "smpte170m",
    "bt470bg": "bt470bg",
    "iec61966-2-1": "srgb",
    "srgb": "srgb",
    "smpte2084": "pq",
    "pq": "pq",
    "smpte st 2084": "pq",
    "arib-std-b67": "hlg",
    "hlg": "hlg",
    "bt2020-10": "bt2020",
    "bt2020-12": "bt2020",
}

#: Transfer functions that positively signal HDR intent, which guards the conditional
#: HDR rules (YouTube preset, register section 3.5).
HDR_TRANSFERS = frozenset({"pq", "hlg"})

_COLOUR_PRIMARIES: dict[str, str] = {
    "bt709": "bt709",
    "bt.709": "bt709",
    "bt2020": "bt2020",
    "bt.2020": "bt2020",
    "bt470bg": "bt470bg",
    "smpte170m": "smpte170m",
    "smpte432": "display-p3",
    "display p3": "display-p3",
    "dci-p3": "dci-p3",
    "smpte431": "dci-p3",
}

_COLOUR_RANGES: dict[str, str] = {
    "tv": "limited",
    "mpeg": "limited",
    "limited": "limited",
    "pc": "full",
    "jpeg": "full",
    "full": "full",
}


def canonical_transfer(raw: str) -> str | None:
    return _TRANSFER_CHARACTERISTICS.get(raw.strip().lower())


def canonical_primaries(raw: str) -> str | None:
    return _COLOUR_PRIMARIES.get(raw.strip().lower())


def canonical_colour_range(raw: str) -> str | None:
    return _COLOUR_RANGES.get(raw.strip().lower())


#: Values inspectors emit that mean "no colour description present in the stream".
COLOUR_ABSENT_TOKENS = frozenset({"unknown", "unspecified", "reserved", "", "n/a"})


def is_colour_absent(raw: str) -> bool:
    return raw.strip().lower() in COLOUR_ABSENT_TOKENS


# ---------------------------------------------------------------------------
# Equivalence — same fact, different spelling
# ---------------------------------------------------------------------------
#
# ffprobe and MediaInfo routinely describe the *same* value in different words:
# "stereo" vs "L R", "Profile 0" vs "0", "bt2020nc" vs "BT.2020 non-constant".
#
# Treating those as disagreement is not a cosmetic problem. A CONFLICTED field caps rule
# severity at WARN, so a spelling difference would silently downgrade a genuine hard
# requirement -- LinkedIn CTV's "audio must be 2-channel", for instance. These helpers
# decide *agreement*; they never change the value that gets stored and displayed.

_MATRIX_COEFFICIENTS: dict[str, str] = {
    "bt709": "bt709",
    "bt.709": "bt709",
    "bt2020nc": "bt2020ncl",
    "bt2020_ncl": "bt2020ncl",
    "bt.2020 non-constant": "bt2020ncl",
    "bt2020 non-constant": "bt2020ncl",
    "bt2020c": "bt2020cl",
    "bt2020_cl": "bt2020cl",
    "bt.2020 constant": "bt2020cl",
    "smpte170m": "smpte170m",
    "bt601": "smpte170m",
    "bt.601": "smpte170m",
    "smpte240m": "smpte240m",
    "fcc": "fcc",
    "gbr": "rgb",
    "rgb": "rgb",
    "ycgco": "ycgco",
}


def canonical_colour_matrix(raw: str) -> str | None:
    """Canonical matrix-coefficients token, or None if unmapped."""
    return _MATRIX_COEFFICIENTS.get(raw.strip().lower())


#: Channel layouts, as each inspector spells them.
_CHANNEL_LAYOUTS: dict[str, str] = {
    "mono": "mono",
    "m": "mono",
    "c": "mono",
    "1": "mono",
    "stereo": "stereo",
    "l r": "stereo",
    "2": "stereo",
    "5.1": "5.1",
    "l r c lfe ls rs": "5.1",
    "l r c lfe lb rb": "5.1",
    "5.1(side)": "5.1",
    "7.1": "7.1",
    "l r c lfe ls rs lb rb": "7.1",
    "quad": "quad",
    "l r lb rb": "quad",
}


def canonical_channel_layout(raw: str) -> str | None:
    return _CHANNEL_LAYOUTS.get(raw.strip().lower())


def _profile_key(raw: str) -> str:
    """Reduce a codec profile to its comparable core.

    MediaInfo writes "High@L4.0" and "Profile 2"; ffprobe writes "High" and "Profile 2".
    The level suffix and the redundant "Profile " prefix are noise for comparison.
    """
    text = raw.strip().lower()
    text = text.split("@", 1)[0].strip()
    if text.startswith("profile "):
        text = text[len("profile ") :].strip()
    return text


def values_agree(property_path: str, left: object, right: object) -> bool:
    """Whether two inspector readings of one property describe the same fact.

    Falls back to equality for properties with no known spelling variance.
    """
    if left == right:
        return True

    # Set-valued: ffprobe reports a container *family* ("matroska,webm" -> {mkv, webm})
    # while MediaInfo names the specific one ("WebM" -> {webm}). A subset is a narrower
    # description of the same container, not a contradiction.
    if isinstance(left, frozenset | set) and isinstance(right, frozenset | set):
        return bool(left & right)

    if not isinstance(left, str) or not isinstance(right, str):
        return False

    if property_path == "video.colour_space":
        a, b = canonical_colour_matrix(left), canonical_colour_matrix(right)
        return a is not None and a == b
    if property_path == "audio.channel_layout":
        a, b = canonical_channel_layout(left), canonical_channel_layout(right)
        return a is not None and a == b
    if property_path == "video.profile":
        return _profile_key(left) == _profile_key(right)
    return False
