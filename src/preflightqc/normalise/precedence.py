"""Per-field inspector precedence.

This is **data**, not a chain of conditionals (ARCHITECTURE-V1.md section 5.3.1).
Changing which inspector wins a field is a table edit.

Sourced from `docs/sources/SOURCE-REGISTER.md` section 5, which was derived from the two
dependency research documents. Those entries are **documented, not yet measured** --
the Phase 1 spike that would verify them is blocked on the inspector binaries
(`docs/planning/SPIKE-01-INSPECTOR-FINDINGS.md`). Revising an entry after the spike runs
is a one-line change here, which is exactly why this is a table.

The general rule: ffprobe is primary for structured stream parameters; MediaInfo is the
gap-filler for the handful of fields ffprobe handles weakly.
"""

from __future__ import annotations

from collections.abc import Mapping

FFPROBE = "ffprobe"
MEDIAINFO = "mediainfo"

#: The default order when a field is not listed below.
DEFAULT_ORDER: tuple[str, ...] = (FFPROBE, MEDIAINFO)

#: Fields where MediaInfo is the documented better source.
#:
#: - scan_type / field order: ffprobe frequently reports `unknown`; MediaInfo derives
#:   from container atoms. (Register gap G-3 -- advisory in both cases.)
#: - frame_rate_mode: MediaInfo signals CFR/VFR directly. (Gap G-5.)
#: - faststart: ffprobe exposes no direct field; MediaInfo has `IsStreamable`.
#: - hdr_format / dolby_vision: MediaInfo gives clean profile naming where ffprobe
#:   exposes only raw side data.
_PRECEDENCE: Mapping[str, tuple[str, ...]] = {
    "container.faststart": (MEDIAINFO, FFPROBE),
    "video.scan_type": (MEDIAINFO, FFPROBE),
    "video.frame_rate_mode": (MEDIAINFO, FFPROBE),
    "video.hdr_format": (MEDIAINFO, FFPROBE),
    "video.dolby_vision": (MEDIAINFO, FFPROBE),
    "video.chroma_subsampling": (FFPROBE, MEDIAINFO),
    "video.bit_depth": (FFPROBE, MEDIAINFO),
    "video.max_cll": (MEDIAINFO, FFPROBE),
    "video.max_fall": (MEDIAINFO, FFPROBE),
}


def order_for(property_path: str) -> tuple[str, ...]:
    """The inspector preference order for a property path."""
    return _PRECEDENCE.get(property_path, DEFAULT_ORDER)


def prefers(property_path: str, inspector: str) -> int:
    """Rank of an inspector for a property; lower wins. Unlisted inspectors rank last."""
    order = order_for(property_path)
    return order.index(inspector) if inspector in order else len(order)


#: Relative tolerance below which two numeric observations count as agreement rather
#: than conflict.
#:
#: Inspectors routinely differ in the last digit of a duration or bitrate because they
#: round differently, and MediaInfo estimates bitrate from size/duration when the
#: container omits it. Treating that as CONFLICTED would cap severity at WARN for
#: genuinely FAIL-class numeric rules -- a real correctness loss for cosmetic
#: disagreement. Beyond this tolerance the difference is substantive and is preserved.
NUMERIC_AGREEMENT_TOLERANCE = 0.02

#: Absolute tolerance for durations in seconds, applied alongside the relative one, so
#: that very short clips are not flagged over a millisecond of rounding.
DURATION_AGREEMENT_SECONDS = 0.05
