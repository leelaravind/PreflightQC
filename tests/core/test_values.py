"""Phase 2 — the three-valued field (P2-A2, P2-A3, P2-A8)."""

from __future__ import annotations

import pytest

from preflightqc.core.values import (
    FieldNotKnownError,
    FieldState,
    MetaField,
    Provenance,
    absent_reason,
    computed,
)

PROV = Provenance(inspector="ffprobe", field_path="streams[0].bit_rate")


def test_known_field_exposes_its_value_and_provenance() -> None:
    field = MetaField.known(2_500_000, PROV)
    assert field.is_known
    assert field.value == 2_500_000
    assert field.provenance is PROV


def test_reading_value_of_an_absent_field_raises_rather_than_defaulting() -> None:
    """The core guarantee: there is no implicit zero to compare against."""
    for field in (
        MetaField[int].not_present(),
        MetaField[int].undetermined("inspector said unknown"),
        MetaField.conflicted((1, PROV), (2, PROV)),
    ):
        with pytest.raises(FieldNotKnownError):
            _ = field.value


def test_not_present_and_undetermined_are_distinct_states() -> None:
    """P2-A3 — 'absent from the file' and 'we could not tell' are different facts."""
    missing = MetaField[int].not_present()
    unknown = MetaField[int].undetermined("field_order reported as unknown")

    assert missing.state is FieldState.NOT_PRESENT
    assert unknown.state is FieldState.UNDETERMINED
    assert missing.state is not unknown.state
    assert missing.is_absent and unknown.is_absent
    assert absent_reason(missing) != absent_reason(unknown)


def test_absent_bitrate_is_not_present_never_zero() -> None:
    """P2-A2 — the defect this whole module exists to prevent."""
    field = MetaField[int].not_present()
    assert field.or_none() is None
    assert field.or_none() != 0
    assert "not present" in field.describe()


def test_or_none_and_unwrap_or_never_raise() -> None:
    field = MetaField[int].undetermined("no colour description")
    assert field.or_none() is None
    assert field.unwrap_or(-1) == -1


def test_conflicted_preserves_every_observation() -> None:
    a = Provenance(inspector="ffprobe", field_path="streams[0].width")
    b = Provenance(inspector="mediainfo", field_path="Video.Width")
    field = MetaField.conflicted((1080, a), (1088, b))

    assert field.is_conflicted
    assert field.conflict_values() == (1080, 1088)
    assert {p.inspector for _, p in field.conflict} == {"ffprobe", "mediainfo"}
    assert "disagree" in field.describe()


def test_conflicted_requires_at_least_two_observations() -> None:
    with pytest.raises(ValueError, match="at least two"):
        MetaField.conflicted((1080, PROV))


def test_describe_never_renders_absence_as_blank_or_zero() -> None:
    """Spec 15 — a report must never show a value the tool did not measure."""
    for field in (MetaField[int].not_present(), MetaField[int].undetermined("reason")):
        rendered = field.describe()
        assert rendered.strip()
        assert rendered not in {"0", "None", ""}


def test_derived_provenance_is_flagged() -> None:
    """P2-A5/spec 9.6.4 — reports must disclose computed values as computed."""
    prov = computed("video.display_aspect_ratio", derived_from=("video.width", "video.height"))
    assert prov.is_derived
    assert "derived from" in prov.describe()
    assert not PROV.is_derived


def test_undetermined_retains_the_raw_value_it_could_not_map() -> None:
    """P2-A9 — an unmapped token is never coerced, but is not thrown away either."""
    field = MetaField[str].undetermined("pixel format not recognised", raw="yuv420p16xx")
    assert field.raw == "yuv420p16xx"
    assert field.or_none() is None


def test_absent_reason_rejects_a_known_field() -> None:
    with pytest.raises(ValueError, match="not absent"):
        absent_reason(MetaField.known(1, PROV))
