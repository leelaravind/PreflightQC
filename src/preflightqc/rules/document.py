"""Preset documents and rule records.

A preset is **data**: a named, versioned document containing a rule set for one delivery
surface (spec 11.1). These dataclasses are the in-memory form after validation. Nothing
here knows what Instagram or TikTok is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from preflightqc.rules.finding import SourceReference
from preflightqc.rules.severity import Classification, Severity


@dataclass(frozen=True, slots=True)
class Guard:
    """An `applies_when` predicate.

    A guard that evaluates false causes the rule to be **skipped**, never failed
    (spec 11.3.5). A guard whose own property is absent also evaluates false: we cannot
    confirm the rule applies, so we do not apply it. That direction is deliberate --
    the alternative would let an unmeasurable guard turn into a spurious failure.
    """

    property_path: str
    operator: str
    expected: Any = None
    tolerance: float = 0.0
    relative_tolerance: bool = False


@dataclass(frozen=True, slots=True)
class RuleRecord:
    """One evaluable constraint. Spec 11.2."""

    rule_id: str
    platform: str
    preset_id: str
    property_path: str
    operator: str
    expected: Any
    classification: Classification
    severity: Severity
    explanation: str
    source: SourceReference
    last_verified_date: str
    tolerance: float = 0.0
    relative_tolerance: bool = False
    guards: tuple[Guard, ...] = ()
    message_pass: str | None = None
    message_fail: str | None = None
    enabled: bool = True
    measurable_offline: bool = True
    #: Free-text note surfaced with the finding, used to carry documented caveats such
    #: as "not measured by PreflightQC V1" or a preserved source conflict.
    note: str | None = None

    @property
    def is_never_fail(self) -> bool:
        return self.severity is not Severity.FAIL


@dataclass(frozen=True, slots=True)
class PresetDocument:
    """A validated preset. Spec 6.6."""

    preset_id: str
    platform: str
    display_name: str
    description: str
    ruleset_version: str
    last_verified_date: str
    rules: tuple[RuleRecord, ...]
    sources: tuple[SourceReference, ...] = ()
    caveats: tuple[str, ...] = ()
    #: "shipped" for platform presets, "custom" for locally authored profiles. Reports
    #: from a custom profile print the profile name, never a platform name (spec 16.5).
    origin: str = "shipped"
    byte_convention: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_custom(self) -> bool:
        return self.origin == "custom"

    @property
    def enabled_rules(self) -> tuple[RuleRecord, ...]:
        return tuple(rule for rule in self.rules if rule.enabled)

    def rule_ids(self) -> frozenset[str]:
        return frozenset(rule.rule_id for rule in self.rules)

    def failing_rules(self) -> tuple[RuleRecord, ...]:
        """Rules that can produce FAIL. Used by the corpus coverage check."""
        return tuple(rule for rule in self.enabled_rules if rule.severity is Severity.FAIL)


@dataclass(frozen=True, slots=True)
class PresetCatalog:
    """Every preset available to the user, shipped and custom."""

    presets: tuple[PresetDocument, ...]
    #: Presets that failed to load, with the reason. Surfaced to the user rather than
    #: silently swallowed (spec 23).
    rejected: tuple[tuple[str, str], ...] = ()

    def by_id(self, preset_id: str) -> PresetDocument | None:
        return next((p for p in self.presets if p.preset_id == preset_id), None)

    def by_platform(self) -> dict[str, tuple[PresetDocument, ...]]:
        grouped: dict[str, list[PresetDocument]] = {}
        for preset in self.presets:
            grouped.setdefault(preset.platform, []).append(preset)
        return {
            platform: tuple(sorted(items, key=lambda p: p.display_name))
            for platform, items in sorted(grouped.items())
        }
