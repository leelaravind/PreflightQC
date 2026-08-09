"""Phase 3 — every malformed-preset class must be rejected whole (P3-A1..A4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from factories import preset_payload, rule, source_entry
from preflightqc.rules.loader import PresetError, build_preset, load_catalog, load_preset_file


class TestSchemaViolations:
    def test_missing_required_top_level_field(self) -> None:
        payload = preset_payload()
        del payload["ruleset_version"]
        with pytest.raises(PresetError, match="schema violation"):
            build_preset(payload)

    def test_missing_required_rule_field(self) -> None:
        bad = rule()
        del bad["explanation"]
        with pytest.raises(PresetError, match="schema violation"):
            build_preset(preset_payload(rules=[bad]))

    def test_unknown_top_level_field_is_rejected(self) -> None:
        """additionalProperties:false — a typo must not be silently ignored."""
        with pytest.raises(PresetError, match="schema violation"):
            build_preset(preset_payload(unexpected_field="oops"))

    def test_malformed_date_is_rejected(self) -> None:
        with pytest.raises(PresetError, match="schema violation"):
            build_preset(preset_payload(last_verified_date="August 2026"))

    def test_empty_rule_list_is_rejected(self) -> None:
        with pytest.raises(PresetError, match="schema violation"):
            build_preset(preset_payload(rules=[]))

    def test_missing_sources_block_is_rejected(self) -> None:
        with pytest.raises(PresetError, match="schema violation"):
            build_preset(preset_payload(sources=[]))


class TestSemanticViolations:
    def test_unknown_property_path(self) -> None:
        """P3-A3 — caught at load, not as a mysterious runtime failure on some file."""
        with pytest.raises(PresetError, match="unknown property path"):
            build_preset(preset_payload(rules=[rule(property_path="video.made_up_field")]))

    def test_unknown_operator(self) -> None:
        with pytest.raises(PresetError, match="schema violation"):
            build_preset(preset_payload(rules=[rule(operator="approximately")]))

    def test_range_operator_with_a_scalar_expected_value(self) -> None:
        with pytest.raises(PresetError, match="range operator"):
            build_preset(preset_payload(rules=[rule(operator="range", expected=1920)]))

    def test_range_operator_with_neither_bound(self) -> None:
        with pytest.raises(PresetError, match="at least one of min or max"):
            build_preset(preset_payload(rules=[rule(operator="range", expected={})]))

    def test_list_operator_with_a_scalar_expected_value(self) -> None:
        with pytest.raises(PresetError, match="non-empty array"):
            build_preset(preset_payload(rules=[rule(operator="in", expected="mp4")]))

    def test_scalar_operator_with_a_list_expected_value(self) -> None:
        with pytest.raises(PresetError, match="scalar value"):
            build_preset(preset_payload(rules=[rule(operator="lte", expected=[1, 2])]))

    def test_duplicate_rule_id(self) -> None:
        with pytest.raises(PresetError, match="duplicate rule_id"):
            build_preset(preset_payload(rules=[rule("same.id"), rule("same.id")]))

    def test_undeclared_source_ref(self) -> None:
        """Spec 12 — every rule must trace to a declared source."""
        with pytest.raises(PresetError, match="not declared in the preset's sources"):
            build_preset(preset_payload(rules=[rule(source_ref="S99")]))

    def test_duplicate_source_ref(self) -> None:
        with pytest.raises(PresetError, match="duplicate source_ref"):
            build_preset(preset_payload(sources=[source_entry("S1"), source_entry("S1")]))

    def test_guard_targeting_an_unknown_property(self) -> None:
        with pytest.raises(PresetError, match="guard targets unknown property"):
            build_preset(
                preset_payload(
                    rules=[
                        rule(
                            applies_when=[
                                {"property": "video.nonexistent", "operator": "eq", "expected": 1}
                            ]
                        )
                    ]
                )
            )

    def test_guard_with_a_malformed_shape(self) -> None:
        with pytest.raises(PresetError, match="guard is invalid"):
            build_preset(
                preset_payload(
                    rules=[
                        rule(
                            applies_when=[
                                {"property": "video.width", "operator": "range", "expected": 1920}
                            ]
                        )
                    ]
                )
            )


class TestAllOrNothing:
    def test_one_bad_rule_rejects_every_rule(self) -> None:
        """P3-A4 — a preset must never partially load."""
        payload = preset_payload(
            rules=[rule("fine.one"), rule("broken", property_path="nope.nope"), rule("fine.two")]
        )
        with pytest.raises(PresetError):
            build_preset(payload)

    def test_the_error_names_the_offending_rule(self) -> None:
        payload = preset_payload(rules=[rule("fine.one"), rule("broken", operator="lte", expected=[1])])
        with pytest.raises(PresetError) as exc:
            build_preset(payload)
        assert "broken" in str(exc.value)


class TestCatalogLoading:
    def test_a_rejected_preset_does_not_disable_the_others(self, tmp_path: Path) -> None:
        """Spec 23 — the application stays usable."""
        (tmp_path / "good.json").write_text(
            json.dumps(preset_payload(preset_id="good_preset")), encoding="utf-8"
        )
        (tmp_path / "bad.json").write_text(
            json.dumps(
                preset_payload(
                    preset_id="bad_preset",
                    rules=[rule(classification="RECOMMENDATION", severity="FAIL")],
                )
            ),
            encoding="utf-8",
        )
        catalog = load_catalog([tmp_path])
        assert [p.preset_id for p in catalog.presets] == ["good_preset"]
        assert len(catalog.rejected) == 1
        assert "bad" in catalog.rejected[0][0]

    def test_a_custom_profile_cannot_shadow_a_shipped_preset(self, tmp_path: Path) -> None:
        """Spec 16 / architecture section 7."""
        (tmp_path / "shadow.json").write_text(
            json.dumps(preset_payload(preset_id="ig_reels")), encoding="utf-8"
        )
        catalog = load_catalog([tmp_path], reserved_ids=frozenset({"ig_reels"}))
        assert catalog.presets == ()
        assert "may not shadow" in catalog.rejected[0][1]

    def test_invalid_json_is_reported_not_raised(self, tmp_path: Path) -> None:
        (tmp_path / "broken.json").write_text("{ not json", encoding="utf-8")
        catalog = load_catalog([tmp_path])
        assert catalog.presets == ()
        assert "not valid JSON" in catalog.rejected[0][1]

    def test_a_missing_directory_is_not_an_error(self, tmp_path: Path) -> None:
        catalog = load_catalog([tmp_path / "does-not-exist"])
        assert catalog.presets == ()
        assert catalog.rejected == ()


def test_load_preset_file_rejects_a_non_object_document(tmp_path: Path) -> None:
    path = tmp_path / "list.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(PresetError, match="must be a JSON object"):
        load_preset_file(path)


def test_schema_contains_no_remote_reference() -> None:
    """Spec 18 — schema resolution must never be able to reach the network."""
    from preflightqc.rules.loader import SCHEMA_PATH

    text = SCHEMA_PATH.read_text(encoding="utf-8")
    payload = json.loads(text)

    def walk(node: object) -> None:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str):
                assert ref.startswith("#"), f"remote $ref found: {ref}"
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
