"""Preset loading and validation.

The loader **fails closed**. A preset is rejected *wholly*, never partially (spec 23),
and the rejection message names the offending rule so the user can act on it.

Order of checks matters: schema first (cheap, catches shape errors), then semantics
(property paths, operator shapes, uniqueness), then the severity ceiling. The ceiling is
last because it is the one that must never be skipped, and putting it last means every
earlier failure has already produced a clearer message.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema

from preflightqc.core.model import is_known_property
from preflightqc.rules import operators
from preflightqc.rules import severity as sev
from preflightqc.rules.document import Guard, PresetCatalog, PresetDocument, RuleRecord
from preflightqc.rules.finding import SourceReference
from preflightqc.rules.severity import Classification, Severity

SCHEMA_PATH = Path(__file__).parent / "schema" / "preset.schema.json"


class PresetError(ValueError):
    """A preset could not be loaded. Carries the preset id and the offending rule."""

    def __init__(self, preset_id: str, message: str, rule_id: str | None = None) -> None:
        self.preset_id = preset_id
        self.rule_id = rule_id
        location = f"preset '{preset_id}'" + (f", rule '{rule_id}'" if rule_id else "")
        super().__init__(f"{location}: {message}")


@lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return payload


@lru_cache(maxsize=1)
def _validator() -> jsonschema.protocols.Validator:
    schema = _schema()
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    # No registry/resolver is supplied: the schema contains no remote $ref, so schema
    # resolution can never reach the network. Spec 18 requires the application to work
    # with all outbound access blocked.
    return validator_cls(schema)


@dataclass(frozen=True, slots=True)
class LoadResult:
    """Outcome of loading a directory of presets."""

    catalog: PresetCatalog

    @property
    def ok(self) -> bool:
        return not self.catalog.rejected


def _source_map(payload: Mapping[str, Any], preset_id: str) -> dict[str, SourceReference]:
    sources: dict[str, SourceReference] = {}
    for entry in payload["sources"]:
        ref = entry["source_ref"]
        if ref in sources:
            raise PresetError(preset_id, f"duplicate source_ref '{ref}'")
        sources[ref] = SourceReference(
            source_ref=ref,
            title=entry["title"],
            url=entry["url"],
            access_date=entry["access_date"],
            confidence=entry["confidence"],
        )
    return sources


def _build_guard(raw: Mapping[str, Any], preset_id: str, rule_id: str) -> Guard:
    path = raw["property"]
    if not is_known_property(path):
        raise PresetError(preset_id, f"guard targets unknown property path '{path}'", rule_id)
    operator_name = raw["operator"]
    try:
        operators.validate_shape(operator_name, raw.get("expected"))
    except operators.OperatorError as exc:
        raise PresetError(preset_id, f"guard is invalid: {exc}", rule_id) from exc
    return Guard(
        property_path=path,
        operator=operator_name,
        expected=raw.get("expected"),
        tolerance=float(raw.get("tolerance", 0.0)),
        relative_tolerance=bool(raw.get("relative_tolerance", False)),
    )


def _build_rule(
    raw: Mapping[str, Any],
    *,
    preset_id: str,
    platform: str,
    sources: Mapping[str, SourceReference],
) -> RuleRecord:
    rule_id = raw["rule_id"]

    property_path = raw["property"]
    if not is_known_property(property_path):
        raise PresetError(preset_id, f"unknown property path '{property_path}'", rule_id)

    operator_name = raw["operator"]
    try:
        operators.validate_shape(operator_name, raw.get("expected"))
    except operators.OperatorError as exc:
        raise PresetError(preset_id, str(exc), rule_id) from exc

    source_ref = raw["source_ref"]
    if source_ref not in sources:
        raise PresetError(
            preset_id,
            f"source_ref '{source_ref}' is not declared in the preset's sources block",
            rule_id,
        )

    classification = Classification(raw["classification"])
    severity = Severity(raw["severity"])

    # THE SEVERITY CEILING. Specification 7.3. A preset that breaks this is rejected
    # whole, before any file is evaluated, which is what makes 7.1 unviolatable.
    if not sev.is_permitted(classification, severity):
        raise PresetError(
            preset_id,
            sev.ceiling_violation_message(rule_id, classification, severity),
            rule_id,
        )

    guards = tuple(
        _build_guard(guard, preset_id, rule_id) for guard in raw.get("applies_when", []) or []
    )

    declared = sources[source_ref]
    return RuleRecord(
        rule_id=rule_id,
        platform=platform,
        preset_id=preset_id,
        property_path=property_path,
        operator=operator_name,
        expected=raw.get("expected"),
        classification=classification,
        severity=severity,
        explanation=raw["explanation"],
        source=SourceReference(
            source_ref=declared.source_ref,
            title=declared.title,
            url=declared.url,
            access_date=declared.access_date,
            confidence=raw["confidence"],
        ),
        last_verified_date=raw["last_verified_date"],
        tolerance=float(raw.get("tolerance", 0.0)),
        relative_tolerance=bool(raw.get("relative_tolerance", False)),
        guards=guards,
        message_pass=raw.get("message_pass"),
        message_fail=raw.get("message_fail"),
        enabled=bool(raw.get("enabled", True)),
        measurable_offline=bool(raw.get("measurable_offline", True)),
        note=raw.get("note"),
    )


def build_preset(payload: Mapping[str, Any]) -> PresetDocument:
    """Validate a parsed preset payload and build the document.

    Raises PresetError on any violation. There is no partial success.
    """
    preset_id = str(payload.get("preset_id", "<unknown>"))

    errors = sorted(_validator().iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.path) or "<document>"
        raise PresetError(preset_id, f"schema violation at {location}: {first.message}")

    platform = payload["platform"]
    sources = _source_map(payload, preset_id)

    seen: set[str] = set()
    rules: list[RuleRecord] = []
    for raw_rule in payload["rules"]:
        rule_id = raw_rule["rule_id"]
        if rule_id in seen:
            raise PresetError(preset_id, f"duplicate rule_id '{rule_id}'", rule_id)
        seen.add(rule_id)
        rules.append(_build_rule(raw_rule, preset_id=preset_id, platform=platform, sources=sources))

    return PresetDocument(
        preset_id=preset_id,
        platform=platform,
        display_name=payload["display_name"],
        description=payload["description"],
        ruleset_version=payload["ruleset_version"],
        last_verified_date=payload["last_verified_date"],
        rules=tuple(rules),
        sources=tuple(sources.values()),
        caveats=tuple(payload.get("caveats", []) or []),
        origin=payload.get("origin", "shipped"),
        byte_convention=payload.get("byte_convention"),
        metadata=dict(payload.get("metadata", {}) or {}),
    )


def load_preset_file(path: Path) -> PresetDocument:
    """Load and validate one preset document from disk."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PresetError(path.stem, f"not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise PresetError(path.stem, "preset document must be a JSON object")
    return build_preset(payload)


def load_catalog(
    directories: Iterable[Path],
    *,
    reserved_ids: frozenset[str] = frozenset(),
) -> PresetCatalog:
    """Load every preset under the given directories.

    A preset that fails validation is recorded in `rejected` and excluded. The others
    remain usable, so one malformed document cannot make the application unusable
    (spec 23).
    """
    presets: list[PresetDocument] = []
    rejected: list[tuple[str, str]] = []
    seen_ids = set(reserved_ids)

    for directory in directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.json")):
            try:
                preset = load_preset_file(path)
            except PresetError as exc:
                rejected.append((str(path), str(exc)))
                continue
            if preset.preset_id in seen_ids:
                rejected.append(
                    (
                        str(path),
                        f"preset id '{preset.preset_id}' is already in use; "
                        "a custom profile may not shadow a shipped preset",
                    )
                )
                continue
            seen_ids.add(preset.preset_id)
            presets.append(preset)

    presets.sort(key=lambda p: (p.platform, p.display_name))
    return PresetCatalog(presets=tuple(presets), rejected=tuple(rejected))
