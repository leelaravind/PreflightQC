"""Inspector spelling equivalence — findings from the real GATE-1 spike.

Every case here was observed running the real ffprobe n8.1.2 and MediaInfo 26.05 over
real media. Before these fixes, all four were reported as inspector *disagreements*.

Why that mattered: a CONFLICTED field caps rule severity at WARN (spec 10.4). So a
purely cosmetic spelling difference would silently downgrade a genuine hard requirement —
LinkedIn CTV's "audio must be 2-channel" would have become a warning because ffprobe
says "stereo" and MediaInfo says "L R".

The opposite property matters just as much: a *real* disagreement must still be
preserved. Both directions are tested.
"""

from __future__ import annotations

import pytest

from factories import build_media, ffprobe_payload, mediainfo_payload
from preflightqc.core import vocabulary as vocab


class TestObservedSpellingVariance:
    """Verbatim value pairs seen from the real binaries."""

    @pytest.mark.parametrize(
        ("prop", "ffprobe_value", "mediainfo_value"),
        [
            ("video.colour_space", "bt2020nc", "BT.2020 non-constant"),
            ("video.profile", "Profile 0", "0"),
            ("video.profile", "Profile 2", "2"),
            ("audio.channel_layout", "stereo", "L R"),
            ("audio.channel_layout", "mono", "M"),
        ],
    )
    def test_the_same_fact_spelled_differently_agrees(
        self, prop: str, ffprobe_value: str, mediainfo_value: str
    ) -> None:
        assert vocab.values_agree(prop, ffprobe_value, mediainfo_value)

    def test_container_family_and_specific_name_agree(self) -> None:
        """ffprobe reports "matroska,webm"; MediaInfo names the specific one, "WebM".

        A subset is a narrower description of the same container, not a contradiction.
        """
        assert vocab.values_agree(
            "container.format", frozenset({"mkv", "webm"}), frozenset({"webm"})
        )

    def test_h264_profile_with_a_level_suffix_agrees(self) -> None:
        """MediaInfo writes "High@L4.0" where ffprobe writes "High"."""
        assert vocab.values_agree("video.profile", "High", "High@L4.0")


class TestRealDisagreementSurvives:
    """The fix must not make everything agree."""

    @pytest.mark.parametrize(
        ("prop", "left", "right"),
        [
            ("video.colour_space", "bt709", "bt2020nc"),
            ("video.profile", "High", "Baseline"),
            ("audio.channel_layout", "stereo", "5.1"),
            ("audio.channel_layout", "mono", "stereo"),
        ],
    )
    def test_genuinely_different_values_still_disagree(
        self, prop: str, left: str, right: str
    ) -> None:
        assert not vocab.values_agree(prop, left, right)

    def test_disjoint_container_sets_still_disagree(self) -> None:
        assert not vocab.values_agree(
            "container.format", frozenset({"mp4"}), frozenset({"avi"})
        )

    def test_a_property_with_no_equivalence_rule_falls_back_to_equality(self) -> None:
        assert vocab.values_agree("video.codec", "h264", "h264")
        assert not vocab.values_agree("video.codec", "h264", "hevc")


class TestThroughTheNormaliser:
    def test_stereo_and_l_r_do_not_produce_a_conflict(self) -> None:
        media = build_media(
            ffprobe=ffprobe_payload(video={}, audio={"channel_layout": "stereo"}),
            mediainfo=mediainfo_payload(video={}, audio={"ChannelLayout": "L R"}),
        )
        audio = media.primary_audio
        assert audio is not None
        assert audio.channel_layout.is_known
        assert audio.channel_layout.value == "stereo"
        assert not media.diagnostics.conflicts

    def test_matroska_family_and_webm_do_not_produce_a_conflict(self) -> None:
        media = build_media(
            ffprobe=ffprobe_payload(format_name="matroska,webm", video={}),
            mediainfo=mediainfo_payload(fmt="WebM", video={}),
        )
        assert media.container.formats.is_known
        assert "webm" in media.container.formats.value

    def test_a_real_channel_count_disagreement_is_still_preserved(self) -> None:
        """The safety property: substantive disagreement must reach the user."""
        media = build_media(
            ffprobe=ffprobe_payload(video={}, audio={"channel_layout": "stereo"}),
            mediainfo=mediainfo_payload(video={}, audio={"ChannelLayout": "L R C LFE Ls Rs"}),
        )
        audio = media.primary_audio
        assert audio is not None
        assert audio.channel_layout.is_conflicted
        assert any(c.property_path == "audio.channel_layout" for c in media.diagnostics.conflicts)

    def test_every_conflicted_field_is_recorded_in_diagnostics(self) -> None:
        """Phase 1 found profile and channel_layout conflicting *silently*.

        A CONFLICTED field with no diagnostic entry never reaches the report, so the
        user is never told the inspectors disagreed.
        """
        media = build_media(
            ffprobe=ffprobe_payload(video={"profile": "High"}, audio={"channel_layout": "stereo"}),
            mediainfo=mediainfo_payload(
                video={"Format_Profile": "Baseline"}, audio={"ChannelLayout": "5.1"}
            ),
        )
        conflicted = {
            "video.profile": media.primary_video.profile,
            "audio.channel_layout": media.primary_audio.channel_layout,
        }
        recorded = {c.property_path for c in media.diagnostics.conflicts}
        for path, field in conflicted.items():
            assert field.is_conflicted, path
            assert path in recorded, f"{path} is CONFLICTED but absent from diagnostics"
