"""Compile a custom profile into a preset document.

The compiled document goes through the *same* loader, schema and severity guard as a
shipped preset. There is no privileged path for user-authored rules: if a compiled
profile would violate the severity ceiling, it is rejected exactly as a malformed
platform preset would be.
"""

from __future__ import annotations

from typing import Any

from preflightqc.profiles.model import CustomProfile, ProfileProperty, PropertySpec
from preflightqc.rules.document import PresetDocument
from preflightqc.rules.loader import build_preset

#: Which model property each configurable profile property targets, and how its expected
#: value is phrased for a finding.
_TARGETS: dict[ProfileProperty, tuple[str, str]] = {
    ProfileProperty.WIDTH: ("video.display_width", "Width"),
    ProfileProperty.HEIGHT: ("video.display_height", "Height"),
    ProfileProperty.ASPECT_RATIO: ("video.display_aspect_ratio", "Aspect ratio"),
    ProfileProperty.CONTAINER: ("container.format", "Container"),
    ProfileProperty.VIDEO_CODEC: ("video.codec", "Video codec"),
    ProfileProperty.FRAME_RATE: ("video.frame_rate", "Frame rate"),
    ProfileProperty.DURATION: ("file.duration_seconds", "Duration"),
    ProfileProperty.FILE_SIZE: ("file.size_bytes", "File size"),
    ProfileProperty.VIDEO_BITRATE: ("video.bitrate", "Video bitrate"),
    ProfileProperty.AUDIO_CODEC: ("audio.codec", "Audio codec"),
    ProfileProperty.AUDIO_SAMPLE_RATE: ("audio.sample_rate", "Audio sample rate"),
    ProfileProperty.AUDIO_CHANNELS: ("audio.channels", "Audio channels"),
}

SOURCE_REF = "CUSTOM"


def _rule_for(
    profile: CustomProfile, prop: ProfileProperty, spec: PropertySpec
) -> dict[str, Any] | None:
    """Build one rule from one configured property, or None if nothing was configured."""
    if not spec.is_configured:
        return None

    property_path, label = _TARGETS[prop]
    base: dict[str, Any] = {
        "rule_id": f"custom.{prop.value}",
        "property": property_path,
        "classification": spec.requirement.classification,
        "severity": spec.requirement.severity,
        "source_ref": SOURCE_REF,
        "confidence": "HIGH",
        "last_verified_date": profile.modified or profile.created or "2026-01-01",
    }
    if spec.tolerance:
        base["tolerance"] = spec.tolerance

    verb = "must be" if spec.requirement.value == "required" else "should be"

    if spec.allowed:
        base["operator"] = "in"
        base["expected"] = list(spec.allowed)
        base["explanation"] = f"{label} {verb} one of: {', '.join(str(v) for v in spec.allowed)}."
    elif spec.exact is not None:
        base["operator"] = "eq"
        base["expected"] = spec.exact
        base["explanation"] = f"{label} {verb} {spec.exact}."
    elif spec.minimum is not None and spec.maximum is not None:
        base["operator"] = "range"
        base["expected"] = {"min": spec.minimum, "max": spec.maximum}
        base["explanation"] = f"{label} {verb} between {spec.minimum} and {spec.maximum}."
    elif spec.minimum is not None:
        base["operator"] = "gte"
        base["expected"] = spec.minimum
        base["explanation"] = f"{label} {verb} at least {spec.minimum}."
    else:
        base["operator"] = "lte"
        base["expected"] = spec.maximum
        base["explanation"] = f"{label} {verb} at most {spec.maximum}."

    base["message_fail"] = (
        f"This file does not meet the '{profile.name}' delivery specification."
        if spec.requirement.value == "required"
        else f"This is a recommendation in the '{profile.name}' delivery specification."
    )
    return base


def compile_profile(profile: CustomProfile) -> PresetDocument:
    """Compile a profile into a validated preset document.

    Raises PresetError if the result would be invalid -- the same failure a malformed
    shipped preset produces.
    """
    rules = [
        rule
        for prop, spec in profile.properties.items()
        if (rule := _rule_for(profile, prop, spec)) is not None
    ]

    if not rules:
        # The schema requires at least one rule. A profile with nothing configured gets
        # an informational placeholder rather than failing to load, so a half-finished
        # profile is still usable and visibly empty.
        rules = [
            {
                "rule_id": "custom.no_properties_configured",
                "property": "file.size_bytes",
                "operator": "present",
                "classification": "UNKNOWN",
                "severity": "INFO",
                "explanation": "This profile has no properties configured, so nothing is checked.",
                "source_ref": SOURCE_REF,
                "confidence": "HIGH",
                "last_verified_date": profile.modified or profile.created or "2026-01-01",
            }
        ]

    payload: dict[str, Any] = {
        "preset_id": profile.profile_id,
        "platform": "Custom",
        "display_name": profile.name,
        "description": profile.notes or f"Custom delivery specification: {profile.name}",
        "origin": "custom",
        "ruleset_version": profile.modified or profile.created or "custom",
        "last_verified_date": profile.modified or profile.created or "2026-01-01",
        "caveats": [
            "This is a locally authored profile, not a platform specification. "
            "Its rules reflect what you configured, not what any platform publishes."
        ],
        "sources": [
            {
                "source_ref": SOURCE_REF,
                "title": f"Custom client profile: {profile.name}"
                + (f" ({profile.client})" if profile.client else ""),
                "url": "local profile",
                "access_date": profile.modified or profile.created or "2026-01-01",
                "confidence": "HIGH",
            }
        ],
        "rules": rules,
    }
    return build_preset(payload)
