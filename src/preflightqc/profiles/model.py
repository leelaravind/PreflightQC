"""Custom client profiles.

A profile is the user's own delivery specification. It compiles to an ordinary preset
document and is evaluated by exactly the same engine as a platform preset -- there is no
second, weaker code path.

The property set here is the **complete V1 set** (spec 16.1). It is deliberately bounded:
the specification is explicit that V1 must not become a broadcast-specification authoring
suite, and the bound is enforced by a test rather than left to judgement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Requirement(Enum):
    """How strictly the user wants a property enforced.

    This maps onto the classification system rather than bypassing it: a property the
    user marks *required* is a HARD_REQUIREMENT for their own specification, and one
    marked *recommended* is a RECOMMENDATION. The severity ceiling therefore applies to
    custom profiles exactly as it does to platform presets.
    """

    REQUIRED = "required"
    RECOMMENDED = "recommended"

    @property
    def classification(self) -> str:
        return "HARD_REQUIREMENT" if self is Requirement.REQUIRED else "RECOMMENDATION"

    @property
    def severity(self) -> str:
        return "FAIL" if self is Requirement.REQUIRED else "WARN"


class ProfileProperty(Enum):
    """The complete configurable property set for V1. Spec 16.1."""

    WIDTH = "width"
    HEIGHT = "height"
    ASPECT_RATIO = "aspect_ratio"
    CONTAINER = "container"
    VIDEO_CODEC = "video_codec"
    FRAME_RATE = "frame_rate"
    DURATION = "duration"
    FILE_SIZE = "file_size"
    VIDEO_BITRATE = "video_bitrate"
    AUDIO_CODEC = "audio_codec"
    AUDIO_SAMPLE_RATE = "audio_sample_rate"
    AUDIO_CHANNELS = "audio_channels"


@dataclass(frozen=True, slots=True)
class PropertySpec:
    """How the user configured one property.

    Exactly one of `allowed`, `exact` or a min/max bound should be set. A property with
    nothing set produces **no rule at all** -- it is simply not checked, and does not
    default to anything (spec 16.2).
    """

    requirement: Requirement = Requirement.REQUIRED
    allowed: tuple[Any, ...] | None = None
    exact: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    tolerance: float = 0.0

    @property
    def is_configured(self) -> bool:
        return any(
            value is not None
            for value in (self.allowed, self.exact, self.minimum, self.maximum)
        )


@dataclass(frozen=True, slots=True)
class CustomProfile:
    """A locally stored custom client specification."""

    profile_id: str
    name: str
    client: str = ""
    notes: str = ""
    created: str = ""
    modified: str = ""
    properties: dict[ProfileProperty, PropertySpec] = field(default_factory=dict)

    @property
    def configured(self) -> dict[ProfileProperty, PropertySpec]:
        return {p: s for p, s in self.properties.items() if s.is_configured}

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "client": self.client,
            "notes": self.notes,
            "created": self.created,
            "modified": self.modified,
            "properties": {
                prop.value: {
                    "requirement": spec.requirement.value,
                    "allowed": list(spec.allowed) if spec.allowed else None,
                    "exact": spec.exact,
                    "minimum": spec.minimum,
                    "maximum": spec.maximum,
                    "tolerance": spec.tolerance,
                }
                for prop, spec in self.properties.items()
            },
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CustomProfile:
        properties: dict[ProfileProperty, PropertySpec] = {}
        for key, raw in (payload.get("properties") or {}).items():
            try:
                prop = ProfileProperty(key)
            except ValueError:
                # An unknown property means the file came from a newer version, or was
                # hand-edited. Ignoring it is safer than failing the whole profile,
                # because the alternative is a user losing their saved specification.
                continue
            allowed = raw.get("allowed")
            properties[prop] = PropertySpec(
                requirement=Requirement(raw.get("requirement", "required")),
                allowed=tuple(allowed) if allowed else None,
                exact=raw.get("exact"),
                minimum=raw.get("minimum"),
                maximum=raw.get("maximum"),
                tolerance=float(raw.get("tolerance", 0.0)),
            )
        return cls(
            profile_id=payload["profile_id"],
            name=payload["name"],
            client=payload.get("client", ""),
            notes=payload.get("notes", ""),
            created=payload.get("created", ""),
            modified=payload.get("modified", ""),
            properties=properties,
        )
