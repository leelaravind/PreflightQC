"""Phase 7 — custom client profiles (P7-A1..A9)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from factories import build_media, ffprobe_payload
from preflightqc.profiles import store
from preflightqc.profiles.compiler import compile_profile
from preflightqc.profiles.model import (
    CustomProfile,
    ProfileProperty,
    PropertySpec,
    Requirement,
)
from preflightqc.rules.engine import evaluate, evaluate_rule
from preflightqc.rules.severity import Classification, Severity


def profile(**properties: PropertySpec) -> CustomProfile:
    return CustomProfile(
        profile_id="custom_0123456789ab",
        name="Acme Q3 Delivery",
        client="Acme Corp",
        properties={ProfileProperty(k): v for k, v in properties.items()},
    )


class TestCompilation:
    def test_a_compiled_profile_passes_the_same_loader_as_a_shipped_preset(self) -> None:
        """P7-A2 — there is no privileged path for user-authored rules."""
        compiled = compile_profile(profile(width=PropertySpec(maximum=1920)))
        assert compiled.preset_id == "custom_0123456789ab"
        assert compiled.is_custom
        assert len(compiled.rules) == 1

    def test_a_required_property_compiles_to_a_hard_requirement(self) -> None:
        compiled = compile_profile(
            profile(width=PropertySpec(maximum=1920, requirement=Requirement.REQUIRED))
        )
        rule = compiled.rules[0]
        assert rule.classification is Classification.HARD_REQUIREMENT
        assert rule.severity is Severity.FAIL

    def test_a_recommended_property_can_only_warn(self) -> None:
        """P7-A4 — the severity ceiling applies to custom profiles too."""
        compiled = compile_profile(
            profile(width=PropertySpec(maximum=1920, requirement=Requirement.RECOMMENDED))
        )
        rule = compiled.rules[0]
        assert rule.classification is Classification.RECOMMENDATION
        assert rule.severity is Severity.WARN

        media = build_media(ffprobe=ffprobe_payload(video={"width": 3840}))
        finding = evaluate_rule(media, rule)
        assert finding is not None
        assert finding.severity is Severity.WARN

    def test_an_unconfigured_property_produces_no_rule(self) -> None:
        """P7-A3 — a property the user did not set is simply not checked."""
        compiled = compile_profile(
            profile(width=PropertySpec(maximum=1920), height=PropertySpec())
        )
        assert [r.property_path for r in compiled.rules] == ["video.display_width"]

    def test_an_empty_profile_still_loads_and_checks_nothing(self) -> None:
        compiled = compile_profile(profile())
        media = build_media(ffprobe=ffprobe_payload(video={}))
        findings = [f for f in evaluate(media, compiled) if f.severity is Severity.FAIL]
        assert findings == []

    @pytest.mark.parametrize(
        ("spec", "operator"),
        [
            (PropertySpec(allowed=("mp4", "mov")), "in"),
            (PropertySpec(exact=1920), "eq"),
            (PropertySpec(minimum=100, maximum=200), "range"),
            (PropertySpec(minimum=100), "gte"),
            (PropertySpec(maximum=200), "lte"),
        ],
    )
    def test_each_configuration_shape_compiles(self, spec: PropertySpec, operator: str) -> None:
        compiled = compile_profile(profile(width=spec))
        assert compiled.rules[0].operator == operator

    def test_every_v1_property_is_compilable(self) -> None:
        """The full spec 16.1 set must actually work, not just be enumerable."""
        for prop in ProfileProperty:
            spec = (
                PropertySpec(allowed=("mp4",))
                if prop in (ProfileProperty.CONTAINER, ProfileProperty.VIDEO_CODEC, ProfileProperty.AUDIO_CODEC)
                else PropertySpec(minimum=1)
            )
            compiled = compile_profile(
                CustomProfile(
                    profile_id="custom_0123456789ab", name="T", properties={prop: spec}
                )
            )
            assert len(compiled.rules) == 1, prop


class TestPropertySetBounds:
    def test_the_property_set_is_exactly_the_v1_list(self) -> None:
        """P7-A9 / spec 16.6 — V1 must not become a broadcast-spec authoring suite."""
        assert {p.value for p in ProfileProperty} == {
            "width",
            "height",
            "aspect_ratio",
            "container",
            "video_codec",
            "frame_rate",
            "duration",
            "file_size",
            "video_bitrate",
            "audio_codec",
            "audio_sample_rate",
            "audio_channels",
        }


class TestStorage:
    def test_save_and_reload_round_trips(self, tmp_path: Path) -> None:
        """P7-A1, P7-A5."""
        original = profile(width=PropertySpec(maximum=1920), container=PropertySpec(allowed=("mp4",)))
        saved = store.save(original, directory=tmp_path)
        assert saved.created and saved.modified

        loaded = store.load(store.profile_path(saved.profile_id, directory=tmp_path))
        assert loaded.name == original.name
        assert loaded.client == original.client
        assert loaded.properties[ProfileProperty.WIDTH].maximum == 1920
        assert loaded.properties[ProfileProperty.CONTAINER].allowed == ("mp4",)

    def test_load_all_separates_good_from_bad(self, tmp_path: Path) -> None:
        store.save(profile(width=PropertySpec(maximum=1920)), directory=tmp_path)
        (tmp_path / "broken.json").write_text("{ not json", encoding="utf-8")

        good, rejected = store.load_all(directory=tmp_path)
        assert len(good) == 1
        assert len(rejected) == 1
        assert "broken.json" in str(rejected[0][0])

    def test_delete_removes_a_profile(self, tmp_path: Path) -> None:
        saved = store.save(profile(width=PropertySpec(maximum=1920)), directory=tmp_path)
        assert store.delete(saved.profile_id, directory=tmp_path)
        assert not store.delete(saved.profile_id, directory=tmp_path)

    def test_a_write_is_atomic(self, tmp_path: Path) -> None:
        """P7-A7 — an interrupted save must never corrupt the previous version."""
        saved = store.save(profile(width=PropertySpec(maximum=1920)), directory=tmp_path)
        path = store.profile_path(saved.profile_id, directory=tmp_path)
        before = path.read_text(encoding="utf-8")

        # A directory in place of the target makes the atomic replace fail.
        broken = tmp_path / "sub"
        broken.mkdir()
        with pytest.raises(store.ProfileError):
            store.export_to(saved, broken)

        assert path.read_text(encoding="utf-8") == before
        assert json.loads(before)["name"] == "Acme Q3 Delivery"

    def test_export_then_import_reproduces_the_profile(self, tmp_path: Path) -> None:
        """P7-A5 — an agency hands a profile to a freelancer."""
        source_dir = tmp_path / "a"
        target_dir = tmp_path / "b"
        source_dir.mkdir()
        target_dir.mkdir()

        original = store.save(
            profile(width=PropertySpec(maximum=1920), duration=PropertySpec(minimum=3, maximum=60)),
            directory=source_dir,
        )
        handoff = tmp_path / "acme.json"
        store.export_to(original, handoff)

        imported = store.import_from(handoff, directory=target_dir)
        assert imported.name == original.name
        assert imported.properties[ProfileProperty.DURATION].maximum == 60

    def test_import_re_ids_on_collision(self, tmp_path: Path) -> None:
        """A freelancer with two agencies' profiles must not have to edit JSON."""
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()
        original = store.save(profile(width=PropertySpec(maximum=1920)), directory=profiles_dir)
        # The handoff file lives outside the store, as it would in reality — otherwise
        # it is itself picked up as a profile and the count is off by one.
        handoff = tmp_path / "copy.json"
        store.export_to(original, handoff)

        imported = store.import_from(handoff, directory=profiles_dir)
        assert imported.profile_id != original.profile_id
        assert len(store.load_all(directory=profiles_dir)[0]) == 2

    def test_a_custom_profile_cannot_take_a_shipped_preset_id(self, tmp_path: Path) -> None:
        """P7-A6 — a report must never say a platform name over private rules."""
        smuggled = CustomProfile(profile_id="ig_reels", name="Sneaky")
        path = tmp_path / "sneaky.json"
        path.write_text(json.dumps(smuggled.to_dict()), encoding="utf-8")

        imported = store.import_from(
            path, directory=tmp_path, reserved_ids=frozenset({"ig_reels"})
        )
        assert imported.profile_id != "ig_reels"
        assert imported.profile_id.startswith("custom_")

    def test_a_non_profile_document_is_rejected(self, tmp_path: Path) -> None:
        path = tmp_path / "other.json"
        path.write_text(json.dumps({"hello": "world"}), encoding="utf-8")
        with pytest.raises(store.ProfileError, match="not a PreflightQC profile"):
            store.load(path)

    def test_an_unknown_property_is_ignored_rather_than_losing_the_profile(
        self, tmp_path: Path
    ) -> None:
        """A profile from a newer version must still be usable, not discarded."""
        payload = profile(width=PropertySpec(maximum=1920)).to_dict()
        payload["properties"]["colour_science"] = {"requirement": "required", "exact": 1}
        path = tmp_path / "future.json"
        path.write_text(json.dumps(payload), encoding="utf-8")

        loaded = store.load(path)
        assert ProfileProperty.WIDTH in loaded.properties
        assert len(loaded.properties) == 1


class TestEvaluation:
    def test_a_custom_profile_validates_a_real_file(self) -> None:
        compiled = compile_profile(
            profile(
                width=PropertySpec(maximum=1920),
                container=PropertySpec(allowed=("mp4",)),
                frame_rate=PropertySpec(minimum=24, maximum=30),
            )
        )
        media = build_media(
            ffprobe=ffprobe_payload(video={"width": 3840, "height": 2160, "avg_frame_rate": "60/1"})
        )
        findings = evaluate(media, compiled)
        failures = {f.rule_id for f in findings if f.severity is Severity.FAIL}
        assert "custom.width" in failures
        assert "custom.frame_rate" in failures

    def test_findings_reference_the_profile_not_a_platform(self) -> None:
        compiled = compile_profile(profile(width=PropertySpec(maximum=1920)))
        media = build_media(ffprobe=ffprobe_payload(video={"width": 3840}))
        finding = evaluate_rule(media, compiled.rules[0])
        assert finding is not None
        assert "Acme Q3 Delivery" in finding.explanation
        assert finding.source.title.startswith("Custom client profile")
